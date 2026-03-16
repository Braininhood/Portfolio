# Booking Pages Performance Optimization

## Problem Identified

The booking pages (especially `/booking/services`) were experiencing slow loading times due to:

1. **Multiple redundant Google API calls**: Postcode validation and geocoding were called repeatedly
2. **N+1 query problem**: Looping through services and making separate database queries for each
3. **No caching**: Geocoding results were fetched from Google API every time
4. **Inefficient queries**: Missing `select_related`/`prefetch_related` optimizations

### Performance Impact

**Before optimization:**
- If there are 10 services and 20 staff areas:
  - 1 postcode validation API call
  - 10 calls to `get_staff_for_postcode` (each validates postcode again)
  - 200 geocoding API calls (20 areas × 10 services)
  - Multiple database queries per service

**After optimization:**
- 1 postcode validation API call
- 1 batch geocoding of unique postcodes (with 24h cache)
- 1-2 optimized database queries
- Pre-calculated staff counts

## Optimizations Implemented

### 1. Geocoding Caching (`_geocode_postcode_cached`)

**Location:** `backend/apps/core/postcode_utils.py`

- Added caching layer for geocoding results
- Cache key: `geocode_postcode_{normalized_postcode}`
- Cache duration: 24 hours (postcodes don't change)
- Uses Django's cache framework (LocMemCache in dev, Redis in production)

**Benefits:**
- First request: API call + cache storage
- Subsequent requests: Instant from cache
- Reduces Google API costs and latency

### 2. Optimized `get_staff_for_postcode`

**Location:** `backend/apps/core/postcode_utils.py`

**Changes:**
- Accepts pre-validated postcode result (avoids re-validation)
- Accepts area coordinates cache (avoids re-geocoding)
- Uses cached geocoding internally
- Single optimized query with `select_related`

**Benefits:**
- No redundant postcode validation
- No redundant geocoding calls
- Faster execution when called multiple times

### 3. Optimized `get_services_for_postcode`

**Location:** `backend/apps/core/postcode_utils.py`

**Changes:**
- Validates postcode ONCE (not per service)
- Batch geocodes all unique postcodes with caching
- Single optimized query instead of N queries
- Uses `select_related('category')` for efficient serialization

**Benefits:**
- Eliminates N+1 query problem
- Reduces API calls from hundreds to ~20-30 (unique postcodes)
- Faster service filtering

### 4. Optimized `by_postcode` View

**Location:** `backend/apps/services/views.py`

**Changes:**
- Validates postcode once and reuses result
- Pre-builds area coordinates cache
- Gets available staff once (reused for filtering and counting)
- Uses `Count` aggregation for staff counts (single query instead of N queries)
- Uses `select_related('category')` for efficient serialization

**Benefits:**
- Single postcode validation
- Single batch geocoding operation
- Single optimized database query for services
- Single aggregated query for staff counts
- Eliminates redundant API calls and queries

## Performance Improvements

### Expected Improvements

- **API Calls**: Reduced from ~200+ to ~20-30 (unique postcodes only)
- **Database Queries**: Reduced from N+1 to 2-3 optimized queries
- **Response Time**: Expected 70-90% reduction in loading time
- **Cache Hit Rate**: After first request, geocoding is instant (24h cache)

### Cache Behavior

- **First Request**: Full API calls + cache storage (normal speed)
- **Subsequent Requests**: Instant from cache (very fast)
- **Cache Expiry**: 24 hours (postcodes rarely change)

## Testing Recommendations

1. **Clear cache and test first request**:
   ```python
   from django.core.cache import cache
   cache.clear()
   ```

2. **Test subsequent requests** (should be much faster)

3. **Monitor Google API usage** (should see significant reduction)

4. **Check database query count** (should see reduction)

## Configuration

### Cache Backend

**Development:** Uses `LocMemCache` (in-memory, per-process)
- Configured in `backend/config/settings/base.py`
- Cache cleared on server restart

**Production:** Can use Redis (if `REDIS_URL` is set)
- Configured in `backend/config/settings/production.py`
- Persistent cache across server restarts
- Better for multi-process deployments

### Cache Settings

```python
# Development (base.py)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'OPTIONS': {'MAX_ENTRIES': 1000},
    }
}

# Production (production.py) - if REDIS_URL is set
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL'),
    }
}
```

## Future Optimizations

1. **Database Indexes**: Ensure indexes on:
   - `StaffArea.postcode`
   - `StaffArea.is_active`
   - `StaffService.service_id`
   - `StaffService.staff_id`

2. **Query Optimization**: Consider using `Prefetch` objects for more complex relationships

3. **Background Jobs**: Consider pre-caching common postcodes in background tasks

4. **API Rate Limiting**: Monitor Google API usage and implement rate limiting if needed

## Files Modified

- `backend/apps/core/postcode_utils.py`
  - Added `_geocode_postcode_cached()` function
  - Optimized `get_staff_for_postcode()` function
  - Optimized `get_services_for_postcode()` function

- `backend/apps/services/views.py`
  - Optimized `by_postcode()` action method

## Notes

- Cache is automatically used by Django's cache framework
- No additional configuration needed for basic usage
- Cache keys are automatically namespaced
- Cache can be cleared manually if needed: `python manage.py shell` → `from django.core.cache import cache` → `cache.clear()`
