from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class ChannelChoices(models.TextChoices):
    NAVER = 'naver', 'Naver'
    COUPANG = 'coupang', 'Coupang'


class DetailCategoryChoices(models.TextChoices):
    PRODUCT_OPTION = 'product_option', 'Product Option'
    PRODUCT_DESCRIPTION = 'product_description', 'Product Description'
    SPECIFICATIONS = 'specifications', 'Specifications'
    USAGE_GUIDE = 'usage_guide', 'Usage Guide'
    INGREDIENTS = 'ingredients', 'Ingredients'
    SIZE_CHART = 'size_chart', 'Size Chart'
    WARRANTY = 'warranty', 'Warranty'
    OTHER = 'other', 'Other'


class ReviewTypeChoices(models.TextChoices):
    TOP = 'top', 'Top Reviews'
    WORST = 'worst', 'Worst Reviews'


class AnalysisStatusChoices(models.TextChoices):
    PENDING = 'pending', 'Pending'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'


class Search(models.Model):
    """Search query made by user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='searches')
    channel = models.CharField(max_length=20, choices=ChannelChoices.choices)
    keyword = models.CharField(max_length=255)
    result_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Searches"
    
    def __str__(self):
        return f"{self.keyword} - {self.channel} ({self.result_count} results)"


class Result(models.Model):
    """Container for search results"""
    search = models.ForeignKey(Search, on_delete=models.CASCADE, related_name='results')
    analysis_status = models.CharField(
        max_length=20, 
        choices=AnalysisStatusChoices.choices, 
        default=AnalysisStatusChoices.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Result for {self.search.keyword}"

class ResultItem(models.Model):
    """Individual product from search results"""
    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='items')
    seller = models.CharField(max_length=255)
    product = models.CharField(max_length=255)
    original_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    shipping = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    review_count = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    library = models.ForeignKey('Library', on_delete=models.SET_NULL, null=True, blank=True)
    product_url = models.URLField(max_length=500, null=True, blank=True)
    product_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    analysis_status = models.CharField(
        max_length=20, 
        choices=AnalysisStatusChoices.choices, 
        default=AnalysisStatusChoices.PENDING
    )

    starred = models.BooleanField(default=False, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product} - {self.seller}"
    
    @property
    def discount_percentage(self):
        if self.original_price and self.sale_price:
            return round(((self.original_price - self.sale_price) / self.original_price * 100), 2)
        return 0

class ResultDetailImage(models.Model):
    """Detail images for product analysis"""
    # result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='detail_images')
    result_item = models.ForeignKey(ResultItem, on_delete=models.CASCADE, related_name='detail_images', null=True, blank=True)
    url = models.URLField(max_length=500)
    section = models.PositiveIntegerField(help_text="Section number for grouping images", blank=True, null=True)
    category = models.CharField(max_length=50, choices=DetailCategoryChoices.choices, blank=True, null=True)
    description = models.TextField(blank=True, help_text="Optional description of the image")
    order = models.PositiveIntegerField(default=0, help_text="Order within section")
    is_analyzed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['section', 'order', 'created_at']
        unique_together = ['result_item', 'url']
    
    def __str__(self):
        return f"Image {self.section}-{self.order} ({self.category})"


class ResultReview(models.Model):
    """Reviews for products"""
    # result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='reviews')
    result_item = models.ForeignKey(ResultItem, on_delete=models.CASCADE, related_name='reviews', null=True)
    review_id = models.CharField(max_length=100, help_text="Original review ID from platform")
    username = models.CharField(max_length=100)
    content = models.TextField()
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    review_type = models.CharField(max_length=10, choices=ReviewTypeChoices.choices)
    date = models.DateTimeField()
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['result_item', 'review_id', 'review_type']
    
    def __str__(self):
        return f"Review by {self.username} - {self.rating}★"


class History(models.Model):
    """User browsing history"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='history')
    result_item = models.ForeignKey(ResultItem, on_delete=models.CASCADE, related_name='history')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Histories"
        unique_together = ['user', 'result_item']  # Prevent duplicates
    
    def __str__(self):
        return f"{self.user.username} viewed {self.result_item.product}"


class Library(models.Model):
    """User's saved collections"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='libraries')
    name = models.CharField(max_length=255)
    memo = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-last_modified']
        verbose_name_plural = "Libraries"
        unique_together = ['user', 'name']  # Prevent duplicate names per user
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
    @property
    def item_count(self):
        return self.items.count()


class LibraryItem(models.Model):
    """Items saved in user's library"""
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='items')
    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='library_items')
    notes = models.TextField(blank=True, help_text="User notes for this item")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['library', 'result']  # Prevent duplicates
    
    def __str__(self):
        return f"{self.library.name} - {self.result}"


class AnalysisResult(models.Model):
    """LLM analysis results for grouped images"""
    # result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='analysis_results')
    result_item = models.ForeignKey(ResultItem, on_delete=models.CASCADE, related_name='analysis_results', default=None)
    section = models.PositiveIntegerField()
    category = models.CharField(max_length=50, choices=DetailCategoryChoices.choices)
    result_json = models.JSONField(default=dict)
    prompt_used = models.TextField(blank=True, help_text="Prompt sent to LLM")
    model_used = models.CharField(max_length=100, blank=True, help_text="LLM model identifier")
    processing_time = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    confidence_score = models.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, 
        choices=AnalysisStatusChoices.choices, 
        default=AnalysisStatusChoices.PENDING
    )
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['result_item', 'section', 'category']
    
    def __str__(self):
        return f"Analysis {self.section}-{self.category} for {self.result_item}"
    
    def get_summary(self):
        """Extract summary from analysis results"""
        if isinstance(self.result_json, dict):
            return self.result_json.get('summary', '')
        return ''
    
    def get_key_points(self):
        """Extract key points from analysis results"""
        if isinstance(self.result_json, dict):
            return self.result_json.get('key_points', [])
        return []