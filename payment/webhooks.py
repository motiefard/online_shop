import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order

# from .tasks import payment_completed


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)
    
    

    if event.type == 'checkout.session.completed':
        session = event.data.object
        print('session.client_reference_id ----------------: ', session.client_reference_id)
        if (
            session.mode == 'payment'
            and session.payment_status == 'paid'
        ):
            try:
                order = Order.objects.get(id=session.client_reference_id)
                # order = Order.objects.get(id=23)
            except Order.DoesNotExist:
                return HttpResponse(status=404)
            
            # mark order as paid
            order.paid = True

            # store Stripe payment ID
            order.stripe_id = session.payment_intent

            order.save()

    return HttpResponse(status=200)