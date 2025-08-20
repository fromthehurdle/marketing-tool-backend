import os
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models 
from django.db.models import Count, Q, Prefetch, Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone
from collections import defaultdict

import os 
import boto3
import uuid
from datetime import datetime
import tempfile


from .models import (
    Search, Result, ResultItem, ResultDetailImage, ResultReview,
    History, Library, LibraryItem, AnalysisResult, Prompts
)
from .serializers import (
    SearchListSerializer, SearchCreateSerializer, SearchDetailSerializer,
    ResultListSerializer, ResultDetailSerializer, ResultCreateSerializer,
    ResultItemListSerializer, ResultItemDetailSerializer, ResultItemCreateSerializer,
    ResultDetailImageSerializer, ResultDetailImageGroupSerializer, 
    ResultDetailImageBulkUpdateSerializer, ResultReviewSerializer, 
    ResultReviewCreateSerializer, AnalysisResultSerializer, HistorySerializer,
    LibraryListSerializer, LibraryCreateUpdateSerializer, LibraryDetailSerializer,
    LibraryItemSerializer, LibraryItemCreateSerializer, AnalysisRequestSerializer,
    AnalysisStatusSerializer
)
from .tasks import run_llm_analysis_task, scrape_naver_task

class SearchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Search CRUD operations
    
    list: Get user's searches with filtering
    retrieve: Get specific search details
    create: Create new search
    update: Update search
    destroy: Delete search
    results: Get search results
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['channel']
    search_fields = ['keyword']
    ordering_fields = ['created_at', 'keyword', 'result_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Search.objects.filter(user=self.request.user).select_related('user')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SearchListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SearchCreateSerializer
        return SearchDetailSerializer
    
    def perform_create(self, serializer):
        search = serializer.save(user=self.request.user)
        scrape_naver_task.delay(search.keyword, search.id)
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get all results for this search"""
        search = self.get_object()
        results = search.results.all().prefetch_related('items')
        serializer = ResultListSerializer(results, many=True, context={'request': request})
        return Response(serializer.data)


class ResultViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Result CRUD operations
    
    list: Get all results with filtering
    retrieve: Get specific result details
    create: Create new result
    update: Update result
    destroy: Delete result
    items: Get result items
    images: Get detail images
    reviews: Get reviews
    analyze: Trigger analysis
    analysis_status: Update analysis status
    image_groups: Get images grouped by section/category
    bulk_update_images: Bulk update image categories
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['analysis_status', 'search__channel']
    search_fields = ['search__keyword']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Result.objects.filter(search__user=self.request.user)
        
        # Optimize queries based on action
        if self.action == 'list':
            queryset = queryset.select_related('search').annotate(
                result_items_count=Count('items'),
                result_analysis_count=Count('analysis_results')
            )
        elif self.action == 'retrieve':
            queryset = queryset.select_related('search__user').prefetch_related(
                'items',
                # 'detail_images',
                # 'reviews',
                # 'analysis_results'
            )
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ResultListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ResultCreateSerializer
        elif self.action == 'analysis_status':
            return AnalysisStatusSerializer
        return ResultDetailSerializer
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get result items"""
        result = self.get_object()
        items = result.items.all()
        serializer = ResultItemListSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get', 'post'])
    def images(self, request, pk=None):
        """Get or create detail images"""
        result = self.get_object()
        
        if request.method == 'GET':
            images = result.detail_images.all().order_by('section', 'order')
            serializer = ResultDetailImageSerializer(images, many=True, context={'request': request})
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = ResultDetailImageSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save(result=result)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def image_groups(self, request, pk=None):
        """Get images grouped by section and category"""
        result = self.get_object()
        images = result.detail_images.all().order_by('section', 'category', 'order')
        
        # Group images by section and category
        groups = defaultdict(lambda: defaultdict(list))
        for image in images:
            groups[image.section][image.category].append(image)
        
        # Convert to serializer format
        grouped_data = []
        for section, categories in groups.items():
            for category, image_list in categories.items():
                grouped_data.append({
                    'section': section,
                    'category': category,
                    'images': image_list,
                    'image_count': len(image_list)
                })
        
        serializer = ResultDetailImageGroupSerializer(grouped_data, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def bulk_update_images(self, request, pk=None):
        """Bulk update image categories and sections"""
        result = self.get_object()
        serializer = ResultDetailImageBulkUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            images_data = serializer.validated_data['images']
            updated_count = 0
            
            for image_data in images_data:
                try:
                    image = result.detail_images.get(id=image_data['id'])
                    image.section = image_data['section']
                    image.category = image_data['category']
                    if 'order' in image_data:
                        image.order = image_data['order']
                    if 'description' in image_data:
                        image.description = image_data['description']
                    image.save()
                    updated_count += 1
                except ResultDetailImage.DoesNotExist:
                    continue
            
            return Response({
                'message': f'Successfully updated {updated_count} images',
                'updated_count': updated_count
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get', 'post'])
    def reviews(self, request, pk=None):
        """Get or create result reviews"""
        result = self.get_object()
        
        if request.method == 'GET':
            reviews = result.reviews.all()
            
            # Filter by review type if specified
            review_type = request.query_params.get('type')
            if review_type in ['top', 'worst']:
                reviews = reviews.filter(review_type=review_type)
            
            serializer = ResultReviewSerializer(reviews, many=True, context={'request': request})
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = ResultReviewCreateSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save(result=result)
                response_serializer = ResultReviewSerializer(
                    serializer.instance, context={'request': request}
                )
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Trigger LLM analysis for grouped images"""
        result = self.get_object()
        serializer = AnalysisRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            sections = serializer.validated_data['sections']
            model = serializer.validated_data.get('model', 'gpt-4')
            prompt_template = serializer.validated_data.get('prompt_template', '')
            
            # Update analysis status
            # result.analysis_status = 'in_progress'
            # result.save()

            if result_item_ids: 
                result_items = result.items.filter(id__in=result_item_ids)
            else: 
                result_items = result.items.all()
            
            result_items.update(analysis_status='in_progress')
            
            # Create analysis results for each section/category combination
            analysis_results = []
            for section_data in sections:
                image_id = section_data['image_id']
                section = section_data['section']
                category = section_data['category']
                
                # Get images for this section/category
                images = result.detail_images.filter(
                    id=image_id, 
                    section=section,
                    category=category
                ).order_by('order')

                
                
                if images.exists():
                    # Create or update analysis result
                    analysis_result, created = AnalysisResult.objects.get_or_create(
                        result=result,
                        section=section,
                        category=category,
                        defaults={
                            'model_used': model,
                            'prompt_used': prompt_template,
                            'result_json': {
                                'status': 'pending',
                                'image_urls': [img.url for img in images],
                                'image_count': images.count()
                            }
                        }
                    )
                    analysis_results.append(analysis_result)
            
            # Here you would typically trigger your LLM analysis task
            serializer = AnalysisResultSerializer(analysis_results, many=True, context={'request': request})
            return Response({
                'message': f'Analysis started for {len(analysis_results)} section/category combinations',
                'analysis_results': serializer.data
            }, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def analysis_status(self, request, pk=None):
        """Update analysis status"""
        result = self.get_object()
        serializer = AnalysisStatusSerializer(result, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResultItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ResultItem CRUD operations
    
    list: Get result items with filtering
    retrieve: Get specific item details
    create: Create new item
    update: Update item
    destroy: Delete item
    add_to_history: Add to user's history
    save_to_library: Save to library
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['seller', 'library']
    search_fields = ['product', 'seller']
    ordering_fields = ['created_at', 'sale_price', 'rating', 'review_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return ResultItem.objects.filter(
            result__search__user=self.request.user
        ).select_related('result__search', 'library')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ResultItemListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ResultItemCreateSerializer
        return ResultItemDetailSerializer
    
    @action(detail=True, methods=['post'])
    def add_to_history(self, request, pk=None):
        """Add item to user's history"""
        item = self.get_object()
        history, created = History.objects.get_or_create(
            user=request.user,
            result_item=item
        )
        
        if not created:
            # Update timestamp if already exists
            history.created_at = timezone.now()
            history.save()
        
        serializer = HistorySerializer(history, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def save_to_library(self, request, pk=None):
        """Save item to a library"""
        item = self.get_object()
        library_id = request.data.get('library_id')
        notes = request.data.get('notes', '')
        
        if not library_id:
            return Response(
                {'error': 'library_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            library = Library.objects.get(id=library_id, user=request.user)
        except Library.DoesNotExist:
            return Response(
                {'error': 'Library not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        library_item, created = LibraryItem.objects.get_or_create(
            library=library,
            result=item.result,
            defaults={'notes': notes}
        )
        
        if not created:
            library_item.notes = notes
            library_item.save()
        
        serializer = LibraryItemSerializer(library_item, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def fix_url(self, url): 
        if "https://https://" in url: 
            url = url.replace("https://https://", "https://")
        return url

    @action(detail=True, methods=['POST'])
    def analyze(self, request, pk=None): 
        """Update analysis status of the result item"""
        result_item = self.get_object()
        serializer = AnalysisRequestSerializer(data=request.data)

        if serializer.is_valid():
            sections = serializer.validated_data['sections']
            model = serializer.validated_data.get('model', 'gpt-4')
            prompt_template = serializer.validated_data.get('prompt_template', '')

            result_item.analysis_status = 'in_progress'
            result_item.save()

            analysis_results = []
            for section_data in sections: 
                section = section_data['section']
                category = section_data['category']

                images = result_item.detail_images.filter(
                    section=section, 
                    category=category
                )

                prompt = Prompts.objects.get(
                    category=category
                )

                if images.exists(): 
                    analysis_result, created = AnalysisResult.objects.get_or_create(
                        result_item=result_item,
                        section=section,
                        category=category,
                        defaults={
                            'model_used': model,
                            'prompt_used': prompt.prompt if prompt else '',
                            'result_json': {
                                'status': 'pending',
                                'image_urls': [self.fix_url(img.url) for img in images],
                                'image_count': images.count()
                            }
                        }
                    )

                    analysis_results.append(analysis_result)
            # Here you would typically trigger your LLM analysis task
            # For now, we'll just return the created analysis results
            print(f"Triggering LLM analysis for {len(analysis_results)} sections/categories")
            run_llm_analysis_task.delay(result_item.id)
            serializer = AnalysisResultSerializer(analysis_results, many=True, context={'request': request})
            return Response({
                'message': f'Analysis started for {len(analysis_results)} section/category combinations',
                'analysis_results': serializer.data
            }, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['post'])
    def upload_image(self, request): 
        try: 
            if 'cropped_image' not in request.FILES: 
                return Response({'error': 'No image file provided'}, status=status.HTTP_400_BAD_REQUEST)
            
            uploaded_file = request.FILES['cropped_image']
            original_image_id = request.data.get('original_image_id')

            # Validate file type
            if not uploaded_file.content_type.startswith('image/'):
                return Response({'error': 'File must be an image'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate unique filename
            file_extension = uploaded_file.name.split('.')[-1] if '.' in uploaded_file.name else 'jpg'
            unique_filename = f"cropped_images/{uuid.uuid4().hex}_{int(datetime.now().timestamp())}.{file_extension}"
            print(f"Uploading image to DigitalOcean Spaces: {unique_filename}")
     

            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file: 
                print(f"Saving uploaded file to temporary path: {temp_file.name}")
                for chunk in uploaded_file.chunks(): 
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            print(f"Temporary file created at: {temp_file_path}")
            print("SPACES REGION_NAME:", os.getenv('SPACES_REGION_NAME'))
            print(f"SPACES SPACE_NAME: {os.getenv('SPACES_SPACE_NAME')}")
            print(f"ENDPOINT URL: https://{os.getenv('SPACES_REGION_NAME')}.digitaloceanspaces.com")
            print(f"SPACES ACCESS_KEY: {os.getenv('SPACES_ACCESS_KEY')}")
            print(f"SPACES SECRET_KEY: {os.getenv('SPACES_SECRET_KEY')}")
            try:
                # Initialize boto3 session and client
                session = boto3.session.Session() 
                client = session.client(
                    's3', 
                    region_name=os.getenv('SPACES_REGION_NAME'), 
                    endpoint_url=f"https://{os.getenv('SPACES_REGION_NAME')}.digitaloceanspaces.com", 
                    aws_access_key_id=os.getenv('SPACES_ACCESS_KEY'), 
                    aws_secret_access_key=os.getenv('SPACES_SECRET_KEY'), 
                )

                # Upload file
                client.upload_file(
                    temp_file_path,  # Local file path
                    os.getenv('SPACES_SPACE_NAME'),  # Bucket name
                    unique_filename,  # Object key (filename in bucket)
                    ExtraArgs={
                        'ACL': 'public-read',
                    }
                )

                spaces_url = f"https://{os.getenv('SPACES_CDN_ENDPOINT')}/{unique_filename}"

                return Response({
                    'success': True,
                    'message': 'Image uploaded successfully',
                    'image_url': spaces_url,
                    'filename': unique_filename,
                    'file_size': uploaded_file.size,
                    'original_image_id': original_image_id
                }, status=status.HTTP_201_CREATED)
            
            finally: 
                if os.path.exists(temp_file_path): 
                    os.unlink(temp_file_path)  # Clean up temp files
        
        except Exception as e: 
            print(f"Error uploading file to digital ocen spaces: {e}")
            return Response({'error': 'Failed to upload image'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True, methods=['get', 'post', 'delete'])
    def images(self, request, pk=None): 
        """Get or create detail images"""
        result_item = self.get_object()

        if request.method == 'GET': 
            images = result_item.detail_images.all().order_by('order', 'created_at', 'section')
            serializer = ResultDetailImageSerializer(images, many=True, context={'request': request})
            return Response(serializer.data)
        
        elif request.method == 'POST': 
            max_order = result_item.detail_images.aggregate(
                max_order=models.Max('order')
            )['max_order'] or 0
            
            data = request.data.copy()
            data['order'] = max_order + 1

            serializer = ResultDetailImageSerializer(data=data, context={'request': request})
            if serializer.is_valid(): 
                serializer.save(result_item=result_item)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE': 
            image_id = request.data.get('image_id')
            if not image_id: 
                return Response({'error': 'image_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            try: 
                image = result_item.detail_images.get(id=image_id)
                image.delete()
                return Response({'message': 'Image deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
            except ResultDetailImage.DoesNotExist:
                return Response({'error': 'Image not found'}, status=status.HTTP_404_NOT_FOUND)
            return Response({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    
    @action(detail=True, methods=['get'])
    def image_groups(self, request, pk=None): 
        """Get images grouped by section and category"""
        result_item = self.get_object()
        images = result_item.detail_images.all().order_by('section', 'category', 'order')

        # Group images by section and category
        groups = defaultdict(lambda: defaultdict(list))
        for image in images: 
            groups[image.section][image.category].append(image)

        # Convert to serializer format 
        grouped_data = []
        for section, categories in groups.items(): 
            for category, image_list in categories.items(): 
                grouped_data.append({
                    'section': section,
                    'category': category,
                    'images': image_list,
                    'image_count': len(image_list)  
                })

        serializer = ResultDetailImageGroupSerializer(grouped_data, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def bulk_update_images(self, request, pk=None): 
        """Bulk update image categories and sections"""
        result_item = self.get_object()
        serializer = ResultDetailImageBulkUpdateSerializer(data=request.data)

        if serializer.is_valid():
            images_data = serializer.validated_data['images']
            updated_count = 0

            for image_data in images_data:
                try:
                    image = result_item.detail_images.get(id=image_data['id'])
                    image.section = image_data['section']
                    image.category = image_data['category']
                    if 'order' in image_data:
                        image.order = image_data['order']
                    if 'description' in image_data:
                        image.description = image_data['description']
                    image.save()
                    updated_count += 1
                except ResultDetailImage.DoesNotExist:
                    continue

            return Response({
                'message': f'Successfully updated {updated_count} images',
                'updated_count': updated_count
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None): 
        """Duplicate a result item"""
        result_item = self.get_object()
        new_item = ResultItem.objects.create(
            result=result_item.result,
            seller=result_item.seller,
            product=result_item.product,
            original_price=result_item.original_price,
            sale_price=result_item.sale_price,
            discount=result_item.discount,
            shipping=result_item.shipping,
            review_count=result_item.review_count,
            rating=result_item.rating,
            product_url=result_item.product_url,
            analysis_status='pending'
        )
        # Copy detail images
        for image in result_item.detail_images.all():
            ResultDetailImage.objects.create(
                result_item=new_item,
                url=image.url,
                section=image.section,
                category=image.category,
                order=image.order,
                description=image.description
            )
        # Copy reviews
        for review in result_item.reviews.all():
            ResultReview.objects.create(
                result_item=new_item,
                content=review.content,
                rating=review.rating,
                review_type=review.review_type,
                created_at=review.created_at
            )
        serializer = ResultItemDetailSerializer(new_item, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def toggle_star(self, request, pk=None): 
        """Toggle starred status of a result item"""
        result_item = self.get_object() 
        result_item.starred = not result_item.starred
        result_item.save()

        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    
    


class HistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for History read operations
    
    list: Get user's browsing history
    retrieve: Get specific history item
    clear: Clear all history
    """
    permission_classes = [IsAuthenticated]
    serializer_class = HistorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['result_item__product', 'result_item__seller']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return History.objects.filter(user=self.request.user).select_related(
            'result_item__result__search'
        )
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Clear all user history"""
        deleted_count = History.objects.filter(user=request.user).delete()[0]
        return Response({
            'message': f'Cleared {deleted_count} history items'
        })


class LibraryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Library CRUD operations
    
    list: Get user's libraries
    retrieve: Get specific library details
    create: Create new library
    update: Update library
    destroy: Delete library
    add_item: Add item to library
    remove_item: Remove item from library
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'memo']
    ordering_fields = ['created_at', 'last_modified', 'name']
    ordering = ['-last_modified']
    
    def get_queryset(self):
        queryset = Library.objects.filter(user=self.request.user)
        
        # if self.action == 'list':
        #     # Use a different name for the annotation to avoid conflict with the property
        #     queryset = queryset.annotate(items_count=Count('items'))
        # elif self.action == 'retrieve':
        #     queryset = queryset.prefetch_related('items__result__search')
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return LibraryListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return LibraryCreateUpdateSerializer
        return LibraryDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add item to library"""
        library = self.get_object()
        serializer = LibraryItemCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Check if user has access to the result
            result = serializer.validated_data['result']
            if result.search.user != request.user:
                return Response(
                    {'error': 'You do not have access to this result'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            library_item, created = LibraryItem.objects.get_or_create(
                library=library,
                result=result,
                defaults={'notes': serializer.validated_data.get('notes', '')}
            )
            
            if not created:
                return Response(
                    {'error': 'Item already exists in library'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            response_serializer = LibraryItemSerializer(library_item, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'])
    def remove_item(self, request, pk=None):
        """Remove item from library"""
        library = self.get_object()
        result_id = request.data.get('result_id')
        
        if not result_id:
            return Response(
                {'error': 'result_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            library_item = LibraryItem.objects.get(
                library=library,
                result_id=result_id
            )
            library_item.delete()
            return Response({'message': 'Item removed from library'})
        except LibraryItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in library'},
                status=status.HTTP_404_NOT_FOUND
            )


class AnalysisResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for AnalysisResult read operations
    
    list: Get analysis results with filtering
    retrieve: Get specific analysis result
    by_result: Get all analysis results for a specific result
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AnalysisResultSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['section', 'category', 'model_used']
    ordering_fields = ['created_at', 'section', 'confidence_score']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return AnalysisResult.objects.filter(
            result_item__result__search__user=self.request.user
        ).select_related('result_item__result__search')
    
    @action(detail=False, methods=['get'])
    def by_result(self, request):
        """Get analysis results for a specific result"""
        result_id = request.query_params.get('result_id')
        if not result_id:
            return Response(
                {'error': 'result_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result_item = ResultItem.objects.get(
                id=result_id, 
            )
        except ResultItem.DoesNotExist:
            return Response(
                {'error': 'Result not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        analysis_results = self.get_queryset().filter(result_item=result_item).order_by('section', 'category')
        serializer = self.get_serializer(analysis_results, many=True)
        return Response(serializer.data)