from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import LetterCaptcha
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def generate_puzzle_captcha(request):
    """Gera um novo captcha com letras"""
    logger.info(f"Generate captcha request - Method: {request.method}, Headers: {dict(request.headers)}")
    
    # Garante que a sessão exista
    if not request.session.session_key:
        request.session.create()
        request.session.modified = True
        logger.info("Created new session")
    
    session_key = request.session.session_key
    logger.info(f"Session key: {session_key}")
    
    # Gera novo captcha
    captcha = LetterCaptcha.generate_captcha(session_key)
    logger.info(f"Generated captcha with letters: {captcha.letters}")
    
    return JsonResponse({
        'success': True,
        'letters': captcha.letters,
        'captcha_id': captcha.id
    })

@csrf_exempt
@require_http_methods(["POST"])
def verify_puzzle_captcha(request):
    """Verifica se o captcha foi resolvido corretamente"""
    logger.info(f"Verify captcha request - Method: {request.method}")
    
    # Garante que a sessão exista
    if not request.session.session_key:
        logger.error("No session key found")
        return JsonResponse({
            'success': False,
            'error': 'Sessão inválida'
        })
    
    session_key = request.session.session_key
    logger.info(f"Session key for verification: {session_key}")
    
    try:
        data = json.loads(request.body)
        user_input = data.get('solution', '')
        logger.info(f"User input: {user_input}")
        
        # Busca o captcha não resolvido
        captcha = LetterCaptcha.objects.get(
            session_key=session_key,
            is_solved=False
        )
        logger.info(f"Found captcha with ID: {captcha.id}")
        
        # Verifica solução
        is_correct = captcha.verify_solution(user_input)
        logger.info(f"Solution correct: {is_correct}")
        
        if is_correct:
            captcha.is_solved = True
            captcha.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Solução incorreta'})
            
    except (LetterCaptcha.DoesNotExist, json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error verifying captcha: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erro ao verificar captcha'
        })
