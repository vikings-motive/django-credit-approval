"""
Health check endpoints for monitoring system status.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.core.cache import cache
import redis
from celery import current_app
import logging

logger = logging.getLogger('api')


@api_view(['GET'])
def health_check(request):
    """
    Basic health check endpoint.
    Returns 200 if the application is running.
    """
    return Response({
        'status': 'healthy',
        'message': 'Credit Approval System is running'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def health_check_detailed(request):
    """
    Detailed health check endpoint.
    Checks all system dependencies:
    - Database connection
    - Redis connection
    - Celery workers
    """
    health_status = {
        'status': 'healthy',
        'services': {}
    }
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['services']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['services']['database'] = {
            'status': 'unhealthy',
            'message': str(e)
        }
        logger.error(f"Database health check failed: {e}")
    
    # Check Redis
    try:
        redis_client = redis.from_url('redis://redis:6379/0')
        redis_client.ping()
        health_status['services']['redis'] = {
            'status': 'healthy',
            'message': 'Redis connection successful'
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['services']['redis'] = {
            'status': 'unhealthy',
            'message': str(e)
        }
        logger.error(f"Redis health check failed: {e}")
    
    # Check Celery
    try:
        # Get active workers
        inspect = current_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            worker_count = len(active_workers)
            health_status['services']['celery'] = {
                'status': 'healthy',
                'message': f'{worker_count} worker(s) active',
                'workers': list(active_workers.keys())
            }
        else:
            health_status['status'] = 'degraded'
            health_status['services']['celery'] = {
                'status': 'degraded',
                'message': 'No active workers found'
            }
    except Exception as e:
        health_status['status'] = 'degraded'
        health_status['services']['celery'] = {
            'status': 'unknown',
            'message': f'Could not check worker status: {str(e)}'
        }
        logger.warning(f"Celery health check failed: {e}")
    
    # Determine HTTP status code
    if health_status['status'] == 'healthy':
        http_status = status.HTTP_200_OK
    elif health_status['status'] == 'degraded':
        http_status = status.HTTP_200_OK  # Still return 200 for degraded
    else:
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(health_status, status=http_status)


@api_view(['GET'])
def readiness_check(request):
    """
    Kubernetes readiness probe endpoint.
    Returns 200 if the application is ready to serve requests.
    """
    try:
        # Quick database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return Response({
            'status': 'ready',
            'message': 'Application is ready to serve requests'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return Response({
            'status': 'not_ready',
            'message': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
def liveness_check(request):
    """
    Kubernetes liveness probe endpoint.
    Returns 200 if the application is alive.
    """
    return Response({
        'status': 'alive',
        'message': 'Application is alive'
    }, status=status.HTTP_200_OK)