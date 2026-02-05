"""
Voice App - Views
Voice command processing endpoints
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .services.intent_parser import IntentParser, ResponseGenerator, Intent
from schemes.services.eligibility_engine import EligibilityEngine
from applications.services.autofill_service import AutoFillService
from applications.models import Application
from schemes.models import Scheme
from core.authentication import get_farmer_from_token


class VoiceProcessView(APIView):
    """
    POST /api/voice/process/
    
    Process voice input text and return appropriate action/response.
    This is the HERO FEATURE - main voice interaction endpoint.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        farmer = get_farmer_from_token(request)
        if not farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get voice text input
        text = request.data.get('text', '').strip()
        if not text:
            return Response({
                'success': False,
                'message': 'No voice text provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        language = farmer.language or 'hindi'
        
        # Parse intent
        parsed = IntentParser.parse(text, language)
        
        # Handle intent
        result = self._handle_intent(parsed, farmer, language)
        
        return Response({
            'success': True,
            'data': {
                'intent': parsed.intent.value,
                'confidence': parsed.confidence,
                'original_text': parsed.original_text,
                'response': result['response'],
                'speech_text': result['speech_text'],
                'action': result.get('action'),
                'data': result.get('data')
            }
        })
    
    def _handle_intent(self, parsed, farmer, language):
        """Handle the parsed intent and return response"""
        intent = parsed.intent
        
        if intent == Intent.SHOW_ELIGIBLE_SCHEMES:
            return self._handle_show_schemes(farmer, language)
        
        elif intent == Intent.APPLY_SCHEME:
            scheme_mention = parsed.entities.get('scheme_mention')
            return self._handle_apply_scheme(farmer, language, scheme_mention)
        
        elif intent == Intent.CHECK_STATUS:
            return self._handle_check_status(farmer, language)
        
        elif intent == Intent.VIEW_PROFILE:
            return self._handle_view_profile(farmer, language)
        
        elif intent == Intent.LIST_APPLICATIONS:
            return self._handle_list_applications(farmer, language)
        
        elif intent == Intent.HELP:
            return self._handle_help(language)
        
        else:
            return self._handle_unknown(language)
    
    def _handle_show_schemes(self, farmer, language):
        """Handle SHOW_ELIGIBLE_SCHEMES intent"""
        if not farmer.is_profile_complete:
            response = ResponseGenerator.get_response(
                Intent.SHOW_ELIGIBLE_SCHEMES, language, 'incomplete_profile'
            )
            return {
                'response': response,
                'speech_text': response,
                'action': 'complete_profile'
            }
        
        eligible = EligibilityEngine.get_eligible_schemes(farmer)
        
        if not eligible:
            response = ResponseGenerator.get_response(
                Intent.SHOW_ELIGIBLE_SCHEMES, language, 'no_schemes'
            )
            return {
                'response': response,
                'speech_text': response,
                'action': None,
                'data': {'schemes': []}
            }
        
        # Build scheme list for speech
        scheme_names = [s['name_localized'] for s in eligible[:3]]
        schemes_text = ', '.join(scheme_names)
        if len(eligible) > 3:
            schemes_text += f' और {len(eligible) - 3} और' if language == 'hindi' else f' and {len(eligible) - 3} more'
        
        response = ResponseGenerator.get_response(
            Intent.SHOW_ELIGIBLE_SCHEMES, language, 'success',
            count=len(eligible), schemes=schemes_text
        )
        
        return {
            'response': response,
            'speech_text': response,
            'action': 'show_schemes',
            'data': {
                'schemes': eligible,
                'count': len(eligible)
            }
        }
    
    def _handle_apply_scheme(self, farmer, language, scheme_mention=None):
        """Handle APPLY_SCHEME intent"""
        # For now, return the first eligible scheme to apply
        # In production, this would need more context
        eligible = EligibilityEngine.get_eligible_schemes(farmer)
        
        if not eligible:
            response = ResponseGenerator.get_response(
                Intent.APPLY_SCHEME, language, 'not_eligible'
            )
            return {
                'response': response,
                'speech_text': response,
                'action': None
            }
        
        # Get first scheme (or match scheme_mention if provided)
        scheme_data = eligible[0]
        scheme = scheme_data['scheme']
        
        # Check if already applied
        existing = Application.objects.filter(farmer=farmer, scheme=scheme).first()
        if existing:
            response = ResponseGenerator.get_response(
                Intent.APPLY_SCHEME, language, 'already_applied'
            )
            return {
                'response': response,
                'speech_text': response,
                'action': 'show_application',
                'data': {
                    'application_id': str(existing.id),
                    'status': existing.status
                }
            }
        
        # Get preview data for confirmation
        preview = AutoFillService.get_form_preview(farmer, scheme)
        
        response = f"क्या आप {scheme_data['name_localized']} के लिए आवेदन करना चाहते हैं?" if language == 'hindi' else \
                   f"Do you want to apply for {scheme_data['name_localized']}?"
        
        return {
            'response': response,
            'speech_text': response,
            'action': 'confirm_apply',
            'data': {
                'scheme_id': str(scheme.id),
                'scheme_name': scheme_data['name_localized'],
                'benefit_amount': scheme_data['benefit_amount'],
                'preview': preview
            }
        }
    
    def _handle_check_status(self, farmer, language):
        """Handle CHECK_STATUS intent"""
        applications = Application.objects.filter(farmer=farmer).select_related('scheme')
        
        if not applications:
            response = ResponseGenerator.get_response(
                Intent.CHECK_STATUS, language, 'no_applications'
            )
            return {
                'response': response,
                'speech_text': response,
                'action': None,
                'data': {'applications': []}
            }
        
        # Build status summary
        pending = applications.filter(status='PENDING').count()
        approved = applications.filter(status='APPROVED').count()
        rejected = applications.filter(status='REJECTED').count()
        
        if language == 'hindi':
            status_summary = f'{pending} पेंडिंग, {approved} स्वीकृत, {rejected} अस्वीकृत'
        else:
            status_summary = f'{pending} pending, {approved} approved, {rejected} rejected'
        
        response = ResponseGenerator.get_response(
            Intent.CHECK_STATUS, language, 'success',
            count=applications.count(), status_summary=status_summary
        )
        
        # Build application list
        app_list = [{
            'id': str(app.id),
            'scheme_name': app.scheme.get_localized_name(language),
            'status': app.status,
            'status_display': app.get_status_display(),
            'applied_on': app.created_at.isoformat()
        } for app in applications]
        
        return {
            'response': response,
            'speech_text': response,
            'action': 'show_applications',
            'data': {
                'applications': app_list,
                'summary': {
                    'total': applications.count(),
                    'pending': pending,
                    'approved': approved,
                    'rejected': rejected
                }
            }
        }
    
    def _handle_view_profile(self, farmer, language):
        """Handle VIEW_PROFILE intent"""
        if language == 'hindi':
            response = f'आपका नाम {farmer.name} है। आपके पास {farmer.land_size} एकड़ जमीन है और आप {farmer.crop_type} उगाते हैं।'
        else:
            response = f'Your name is {farmer.name}. You have {farmer.land_size} acres of land and you grow {farmer.crop_type}.'
        
        return {
            'response': response,
            'speech_text': response,
            'action': 'show_profile',
            'data': {
                'name': farmer.name,
                'phone': farmer.phone,
                'state': farmer.state,
                'district': farmer.district,
                'village': farmer.village,
                'land_size': float(farmer.land_size),
                'crop_type': farmer.crop_type
            }
        }
    
    def _handle_list_applications(self, farmer, language):
        """Handle LIST_APPLICATIONS intent"""
        return self._handle_check_status(farmer, language)
    
    def _handle_help(self, language):
        """Handle HELP intent"""
        response = ResponseGenerator.get_response(Intent.HELP, language)
        return {
            'response': response,
            'speech_text': response,
            'action': 'show_help'
        }
    
    def _handle_unknown(self, language):
        """Handle UNKNOWN intent"""
        response = ResponseGenerator.get_response(Intent.UNKNOWN, language)
        return {
            'response': response,
            'speech_text': response,
            'action': None
        }


class VoiceConfirmView(APIView):
    """
    POST /api/voice/confirm/
    
    Confirm an action from voice interaction (e.g., confirm application).
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        farmer = get_farmer_from_token(request)
        if not farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        action = request.data.get('action')
        scheme_id = request.data.get('scheme_id')
        confirmed = request.data.get('confirmed', False)
        
        if action == 'confirm_apply' and confirmed and scheme_id:
            try:
                scheme = Scheme.objects.get(id=scheme_id)
                application, created = AutoFillService.create_application(farmer, scheme)
                
                if created:
                    language = farmer.language or 'hindi'
                    response = ResponseGenerator.get_response(
                        Intent.APPLY_SCHEME, language, 'success',
                        scheme_name=scheme.get_localized_name(language)
                    )
                    return Response({
                        'success': True,
                        'data': {
                            'application_id': str(application.id),
                            'response': response,
                            'speech_text': response
                        }
                    })
                else:
                    return Response({
                        'success': False,
                        'message': 'Already applied'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Scheme.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Scheme not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': False,
            'message': 'Invalid confirmation'
        }, status=status.HTTP_400_BAD_REQUEST)
