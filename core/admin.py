from django.contrib import admin
from .models import (
    Search, Result, ResultItem, ResultDetailImage, ResultReview,
    History, Library, LibraryItem, AnalysisResult, Prompts
)


@admin.register(Search)
class SearchAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'channel', 'keyword', 'result_count', 'created_at']
    list_filter = ['channel', 'created_at']
    search_fields = ['keyword', 'user__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


class ResultItemInline(admin.TabularInline):
    model = ResultItem
    extra = 0
    fields = ['seller', 'product', 'sale_price', 'rating', 'review_count']
    readonly_fields = ['created_at']


class ResultDetailImageInline(admin.TabularInline):
    model = ResultDetailImage
    extra = 0
    fields = ['url', 'section', 'category', 'order', 'is_analyzed']
    readonly_fields = ['created_at']


class AnalysisResultInline(admin.TabularInline):
    model = AnalysisResult
    extra = 0
    fields = ['section', 'category', 'model_used', 'confidence_score']
    readonly_fields = ['created_at']


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'search', 'analysis_status', 'get_items_count', 'created_at']
    list_filter = ['analysis_status', 'created_at', 'search__channel']
    search_fields = ['search__keyword', 'search__user__username']
    readonly_fields = ['created_at']
    inlines = [ResultItemInline] #, ResultDetailImageInline]
    ordering = ['-created_at']
    
    def get_items_count(self, obj):
        return obj.items.count()
    get_items_count.short_description = 'Items'
    
    # def get_images_count(self, obj):
    #     return obj.detail_images.count()
    # get_images_count.short_description = 'Images'


@admin.register(ResultItem)
class ResultItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'seller', 'sale_price', 'rating', 'review_count', 'created_at']
    list_filter = ['created_at', 'rating']
    search_fields = ['product', 'seller', 'result__search__keyword']
    readonly_fields = ['created_at', 'discount_percentage']
    ordering = ['-created_at']
    
    def discount_percentage(self, obj):
        return f"{obj.discount_percentage:.1f}%"
    discount_percentage.short_description = 'Discount %'


@admin.register(ResultDetailImage)
class ResultDetailImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'result_item', 'section', 'category', 'order', 'is_analyzed', 'created_at']
    list_filter = ['category', 'section', 'is_analyzed', 'created_at']
    search_fields = ['result_item__search__keyword', 'description']
    readonly_fields = ['created_at']
    ordering = ['result_item', 'section', 'order']


@admin.register(ResultReview)
class ResultReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'rating', 'review_type', 'date', 'helpful_count']
    list_filter = ['review_type', 'rating', 'date']
    search_fields = ['username', 'content', 'result_item__result__search__keyword']
    readonly_fields = ['created_at']
    ordering = ['-date']


@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'result_item', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'result_item__product']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


class LibraryItemInline(admin.TabularInline):
    model = LibraryItem
    extra = 0
    fields = ['result', 'notes']
    readonly_fields = ['created_at']


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'user', 'is_public', 'get_item_count', 'last_modified']
    list_filter = ['is_public', 'created_at', 'last_modified']
    search_fields = ['name', 'user__username', 'memo']
    readonly_fields = ['created_at', 'last_modified', 'get_item_count']
    inlines = [LibraryItemInline]
    ordering = ['-last_modified']
    
    def get_item_count(self, obj):
        return obj.item_count
    get_item_count.short_description = 'Items'


@admin.register(LibraryItem)
class LibraryItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'library', 'result', 'created_at']
    list_filter = ['created_at']
    search_fields = ['library__name', 'result__search__keyword', 'notes']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'result_item', 'section', 'category', 'model_used', 'confidence_score', 'created_at']
    list_filter = ['category', 'model_used', 'created_at']
    search_fields = ['result_item__result__search__keyword', 'model_used']
    readonly_fields = ['created_at', 'summary', 'key_points']
    ordering = ['-created_at']
    
    def summary(self, obj):
        return obj.get_summary()[:100] + '...' if obj.get_summary() else 'No summary'
    summary.short_description = 'Summary (first 100 chars)'
    
    def key_points(self, obj):
        points = obj.get_key_points()
        return f"{len(points)} key points" if points else "No key points"
    key_points.short_description = 'Key Points Count'

admin.site.register(Prompts)  # Register Prompts model for admin interface