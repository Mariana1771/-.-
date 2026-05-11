from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('premium/', views.premium_page, name='premium_page'),
    path('premium/stripe/checkout/', views.premium_stripe_checkout, name='premium_stripe_checkout'),
    path('premium/stripe/success/', views.premium_stripe_success, name='premium_stripe_success'),
    path('premium/simple/send-code/', views.premium_simple_send_code, name='premium_simple_send_code'),
    path('premium/simple/confirm/', views.premium_simple_confirm, name='premium_simple_confirm'),
    path('certificates/', views.certificates_page, name='certificates_page'),
    path('certificates/stripe/checkout/', views.certificate_stripe_checkout, name='certificate_stripe_checkout'),
    path('certificates/stripe/success/', views.certificate_stripe_success, name='certificate_stripe_success'),
    path('certificates/simple/send-code/', views.certificate_simple_send_code, name='certificate_simple_send_code'),
    path('certificates/simple/confirm/', views.certificate_simple_confirm, name='certificate_simple_confirm'),
    path('certificates/<slug:program_slug>/', views.certificate_exam_path, name='certificate_exam_path'),
    path('certificates/<slug:program_slug>/certificate/', views.certificate_document, name='certificate_document'),
    path('certificates/<slug:program_slug>/certificate/pdf/', views.certificate_pdf, name='certificate_pdf'),
    path('certificates/<slug:program_slug>/certificate/email/', views.certificate_email, name='certificate_email'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
]
