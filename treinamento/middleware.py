"""
Custom middleware for treinamento application.
"""
import asyncio
from django.core.cache import cache
from django.http import JsonResponse
from asgiref.sync import iscoroutinefunction, markcoroutinefunction


class RateLimitMiddleware:
    """
    Middleware para limitar o número de requisições por IP.
    Protege a API e o login contra ataques de força bruta.
    """
    async_capable = True
    sync_capable = True
    
    # Configurações de rate limiting
    API_RATE_LIMIT = 60  # Requisições por minuto para API
    API_RATE_WINDOW = 60  # Janela de tempo em segundos
    
    LOGIN_RATE_LIMIT = 5  # Tentativas de login por minuto
    LOGIN_RATE_WINDOW = 60  # Janela de tempo em segundos
    LOGIN_BLOCK_DURATION = 300  # Bloqueio de 5 minutos após exceder limite
    
    def __init__(self, get_response):
        self.get_response = get_response
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)
    
    def __call__(self, request):
        # Lógica de process_request
        response = self.handle_rate_limit(request)
        if response:
            return response

        if iscoroutinefunction(self.get_response):
            return self.__acall__(request)
        
        return self.get_response(request)

    async def __acall__(self, request):
        return await self.get_response(request)

    def handle_rate_limit(self, request):
        ip = self.get_client_ip(request)
        
        # Rate limiting para API
        if request.path.startswith('/api/'):
            if self.is_rate_limited(ip, 'api', self.API_RATE_LIMIT, self.API_RATE_WINDOW):
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'message': 'Too many requests. Please try again later.',
                    'retry_after': self.API_RATE_WINDOW
                }, status=429)
        
        # Rate limiting para Login (proteção contra brute force)
        if request.path in ['/login/', '/accounts/login/'] and request.method == 'POST':
            if self.is_blocked(ip, 'login'):
                return JsonResponse({
                    'error': 'Temporarily blocked',
                    'message': 'Too many failed login attempts. Please try again in 5 minutes.',
                    'retry_after': self.LOGIN_BLOCK_DURATION
                }, status=429)
            
            if self.is_rate_limited(ip, 'login', self.LOGIN_RATE_LIMIT, self.LOGIN_RATE_WINDOW):
                # Bloquear o IP por um período mais longo
                self.block_ip(ip, 'login', self.LOGIN_BLOCK_DURATION)
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'message': 'Too many login attempts. Please try again in 5 minutes.',
                    'retry_after': self.LOGIN_BLOCK_DURATION
                }, status=429)
        
        # Rate limiting para registro
        if request.path == '/register/' and request.method == 'POST':
            if self.is_rate_limited(ip, 'register', 3, 60):  # 3 registros por minuto
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'message': 'Too many registration attempts. Please try again later.',
                    'retry_after': 60
                }, status=429)
        
        return None
    
    def get_client_ip(self, request):
        """
        Obtém o IP real do cliente, considerando proxies.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
    
    def is_rate_limited(self, ip, action, limit, window):
        """
        Verifica se o IP atingiu o limite de requisições.
        """
        cache_key = f"rate_limit_{action}_{ip}"
        
        # Obter contagem atual
        attempts = cache.get(cache_key, 0)
        
        if attempts >= limit:
            return True
        
        # Incrementar contador
        cache.set(cache_key, attempts + 1, window)
        return False
    
    def is_blocked(self, ip, action):
        """
        Verifica se o IP está bloqueado.
        """
        cache_key = f"blocked_{action}_{ip}"
        return cache.get(cache_key, False)
    
    def block_ip(self, ip, action, duration):
        """
        Bloqueia um IP por um período específico.
        """
        cache_key = f"blocked_{action}_{ip}"
        cache.set(cache_key, True, duration)


class SecurityHeadersMiddleware:
    """
    Middleware para adicionar headers de segurança às respostas HTTP.
    """
    async_capable = True
    sync_capable = True

    def __init__(self, get_response):
        self.get_response = get_response
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)
    
    def __call__(self, request):
        if iscoroutinefunction(self.get_response):
            return self.__acall__(request)
        
        response = self.get_response(request)
        return self.process_response(request, response)

    async def __acall__(self, request):
        response = await self.get_response(request)
        return self.process_response(request, response)

    def process_response(self, request, response):
        if response is None:
            return response

        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options (proteção contra clickjacking)
        response['X-Frame-Options'] = 'DENY'
        
        # X-XSS-Protection (proteção contra XSS em navegadores antigos)
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer-Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
