from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Search, Result, ResultItem, ResultDetailImage, ResultReview,
    History, Library, LibraryItem, AnalysisResult
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class SearchListSerializer(serializers.ModelSerializer):
    """Serializer for search list view"""
    class Meta:
        model = Search
        fields = ['id', 'channel', 'keyword', 'result_count', 'created_at']
        read_only_fields = ['id', 'result_count', 'created_at']


class SearchCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating searches"""
    class Meta:
        model = Search
        fields = ['id', 'channel', 'keyword']


class SearchDetailSerializer(serializers.ModelSerializer):
    """Detailed search serializer with results"""
    results_count = serializers.IntegerField(source='results.count', read_only=True)
    
    class Meta:
        model = Search
        fields = ['id', 'channel', 'keyword', 'result_count', 'results_count', 'created_at']
        read_only_fields = ['id', 'result_count', 'created_at']


class ResultItemListSerializer(serializers.ModelSerializer):
    """Serializer for result item list view"""
    discount_percentage = serializers.ReadOnlyField()
    keyword  = serializers.CharField(source='result.search.keyword', read_only=True)
    
    class Meta:
        model = ResultItem
        fields = [
            'id', 'seller', 'product', 'original_price', 'sale_price', 
            'discount', 'discount_percentage', 'shipping', 'review_count', 
            'rating', 'product_url', 'created_at', 'result', 'analysis_status', 'keyword', 'starred'
        ]
        read_only_fields = ['id', 'created_at']
    

class ResultItemDetailSerializer(serializers.ModelSerializer):
    """Detailed result item serializer"""
    discount_percentage = serializers.ReadOnlyField()
    image_count = serializers.IntegerField(source='detail_images.count', read_only=True)
    
    class Meta:
        model = ResultItem
        fields = [
            'id', 'seller', 'product', 'original_price', 'sale_price', 
            'discount', 'discount_percentage', 'shipping', 'review_count', 
            'rating', 'library', 'product_url', 'product_date', 'created_at', 'result', 'analysis_status', 'image_count', 'starred'
        ]
        read_only_fields = ['id', 'created_at']


class ResultItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating result items"""
    class Meta:
        model = ResultItem
        fields = [
            'result', 'seller', 'product', 'original_price', 'sale_price', 
            'discount', 'shipping', 'review_count', 'rating', 'library',
            'product_url', 'product_date', 'analysis_status'
        ]
    
    def validate_result(self, value):
        """Ensure user owns the result"""
        if value.search.user != self.context['request'].user:
            raise serializers.ValidationError("You don't have permission to add items to this result.")
        return value


class ResultDetailImageSerializer(serializers.ModelSerializer):
    """Serializer for result detail images"""
    class Meta:
        model = ResultDetailImage
        fields = [
            'id', 'url', 'section', 'category', 'description', 
            'order', 'is_analyzed', 'created_at'
        ]
        read_only_fields = ['id', 'is_analyzed', 'created_at']


class ResultDetailImageGroupSerializer(serializers.Serializer):
    """Serializer for grouping images by section and category"""
    section = serializers.IntegerField()
    category = serializers.CharField()
    images = ResultDetailImageSerializer(many=True, read_only=True)
    image_count = serializers.IntegerField(read_only=True)
    

class ResultDetailImageBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk updating image categories"""
    images = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(),
            required=True
        )
    )
    
    def validate_images(self, value):
        required_fields = ['id', 'section', 'category']
        for image_data in value:
            for field in required_fields:
                if field not in image_data:
                    raise serializers.ValidationError(
                        f"Missing required field '{field}' in image data"
                    )
        return value


class ResultReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating result reviews"""
    class Meta:
        model = ResultReview
        fields = [
            'review_id', 'username', 'content', 'rating', 
            'review_type', 'date', 'helpful_count'
        ]


class ResultReviewSerializer(serializers.ModelSerializer):
    """Serializer for result reviews"""
    class Meta:
        model = ResultReview
        fields = [
            'id', 'review_id', 'username', 'content', 'rating', 
            'review_type', 'date', 'helpful_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AnalysisResultSerializer(serializers.ModelSerializer):
    """Serializer for analysis results"""
    summary = serializers.CharField(source='get_summary', read_only=True)
    key_points = serializers.ListField(source='get_key_points', read_only=True)
    
    class Meta:
        model = AnalysisResult
        fields = [
            'id', 'section', 'category', 'result_json', 'summary', 
            'key_points', 'confidence_score', 'processing_time', 
            'model_used', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ResultCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating results"""
    class Meta:
        model = Result
        fields = ['search', 'analysis_status']
        
    def validate_search(self, value):
        """Ensure user owns the search"""
        if value.user != self.context['request'].user:
            raise serializers.ValidationError("You don't have permission to create results for this search.")
        return value


class ResultListSerializer(serializers.ModelSerializer):
    """Serializer for result list view"""
    search_keyword = serializers.CharField(source='search.keyword', read_only=True)
    search_channel = serializers.CharField(source='search.channel', read_only=True)
    items_count = serializers.SerializerMethodField()
    # analysis_results_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Result
        fields = [
            'id', 'search_keyword', 'search_channel', 
            'items_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_items_count(self, obj):
        # Use annotated field if available, otherwise count directly
        return getattr(obj, 'result_items_count', obj.items.count())
    
    # def get_analysis_results_count(self, obj):
    #     # Use annotated field if available, otherwise count directly
    #     return getattr(obj, 'result_analysis_count', obj.analysis_results.count())


class ResultDetailSerializer(serializers.ModelSerializer):
    """Detailed result serializer with all related data"""
    search = SearchDetailSerializer(read_only=True)
    items = ResultItemListSerializer(many=True, read_only=True)
    # detail_images = ResultDetailImageSerializer(many=True, read_only=True)
    # reviews = ResultReviewSerializer(many=True, read_only=True)
    # analysis_results = AnalysisResultSerializer(many=True, read_only=True)
    
    # Statistics
    items_count = serializers.IntegerField(source='items.count', read_only=True)
    # images_count = serializers.IntegerField(source='detail_images.count', read_only=True)
    # reviews_count = serializers.IntegerField(source='reviews.count', read_only=True)
    # top_reviews_count = serializers.SerializerMethodField()
    # worst_reviews_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Result
        fields = [
            'id', 'search', 'analysis_status', 'items', #'detail_images', 
            'items_count', 
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    # def get_top_reviews_count(self, obj):
    #     return obj.reviews.filter(review_type='top').count()
    
    # def get_worst_reviews_count(self, obj):
    #     return obj.reviews.filter(review_type='worst').count()


class HistorySerializer(serializers.ModelSerializer):
    """Serializer for user history"""
    result_item = ResultItemListSerializer(read_only=True)
    search_keyword = serializers.CharField(source='result_item.result.search.keyword', read_only=True)
    
    class Meta:
        model = History
        fields = ['id', 'result_item', 'search_keyword', 'created_at']
        read_only_fields = ['id', 'created_at']


class LibraryListSerializer(serializers.ModelSerializer):
    """Serializer for library list view"""
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Library
        fields = ['id', 'name', 'memo', 'is_public', 'item_count', 'last_modified', 'created_at']
        read_only_fields = ['id', 'item_count', 'last_modified', 'created_at']
    
    def get_item_count(self, obj):
        # Use annotated field if available, otherwise use the property
        return getattr(obj, 'items_count', obj.item_count)


class ResultForLibrarySerializer(serializers.ModelSerializer):
    """Serializer for result when used in library context"""
    search_keyword = serializers.CharField(source='search.keyword', read_only=True)
    search_channel = serializers.CharField(source='search.channel', read_only=True)
    items_count = serializers.SerializerMethodField()
    # analysis_results_count = serializers.SerializerMethodField()
    result_items = ResultItemListSerializer(source='items', many=True, read_only=True)
    
    class Meta:
        model = Result
        fields = [
            'id', 'search_keyword', 'search_channel', 'analysis_status', 
            'items_count', 'created_at', 'result_items'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_items_count(self, obj):
        return getattr(obj, 'result_items_count', obj.items.count())
    
    # def get_analysis_results_count(self, obj):
    #     return getattr(obj, 'result_analysis_count', obj.analysis_results.count())


class LibraryItemSerializer(serializers.ModelSerializer):
    """Serializer for library items"""
    result = ResultForLibrarySerializer(read_only=True)
    
    class Meta:
        model = LibraryItem
        fields = ['id', 'result', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']


class LibraryCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating libraries"""
    class Meta:
        model = Library
        fields = ['name', 'memo', 'is_public']


class LibraryDetailSerializer(serializers.ModelSerializer):
    """Detailed library serializer with items"""
    items = LibraryItemSerializer(many=True, read_only=True)
    item_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Library
        fields = [
            'id', 'name', 'memo', 'is_public', 'items', 'item_count', 
            'last_modified', 'created_at'
        ]
        read_only_fields = ['id', 'item_count', 'last_modified', 'created_at']


class LibraryItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating library items"""
    class Meta:
        model = LibraryItem
        fields = ['result', 'notes']


class AnalysisRequestSerializer(serializers.Serializer):
    """Serializer for analysis request"""
    sections = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        help_text="List of sections with category groupings to analyze"
    )
    model = serializers.CharField(default='gpt-4', help_text="LLM model to use")
    prompt_template = serializers.CharField(required=False, help_text="Custom prompt template")
    result_item_ids = serializers.ListField(
        child=serializers.IntegerField(), 
        required=False, 
    )
    
    def validate_sections(self, value):
        for section_data in value:
            if 'section' not in section_data or 'category' not in section_data:
                raise serializers.ValidationError(
                    "Each section must have 'section' and 'category' fields"
                )
        return value


class AnalysisStatusSerializer(serializers.ModelSerializer):
    """Serializer for analysis status updates"""
    class Meta:
        model = Result
        fields = ['id', 'analysis_status']
        read_only_fields = ['id']