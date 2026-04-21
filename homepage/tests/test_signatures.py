"""
Tests for the QuoteSignature / quote_sign feature.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User, Group

from homepage.models import QuoteRequest, Quote, QuoteSignature

VALID_SIG = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_group(name):
    group, _ = Group.objects.get_or_create(name=name)
    return group


def make_user(username, group_name=None):
    user = User.objects.create_user(
        username=username, password='testpass123',
        first_name='Test', last_name='User',
        email=f'{username}@test.com',
    )
    if group_name:
        user.groups.add(make_group(group_name))
    return user


def make_quote_request(customer=None):
    return QuoteRequest.objects.create(
        company_name='Test Co', industry='sports_club',
        contact_name='Jane Doe', role='owner', email='jane@test.com',
        product_types='tshirts', quantity_per_style='50-100',
        gender_sizing='unisex', print_method='screen_print',
        print_positions='1', design_files_status='yes_vector',
        desired_delivery='flexible', sample_required='no',
        budget_range='1k-5k', customer=customer,
    )


def make_sent_quote(customer):
    qr = make_quote_request(customer=customer)
    quote = Quote.objects.create(
        quote_request=qr, currency='CHF', status='sent',
        created_by=customer,
    )
    return quote


def sign_url(quote_pk):
    return f'/en/portal/quote/{quote_pk}/sign/'


def print_url(quote_pk):
    return f'/en/portal/staff/quote/{quote_pk}/print/'


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class QuoteSignatureTests(TestCase):

    def setUp(self):
        self.customer = make_user('sig_customer')
        self.staff = make_user('sig_staff', group_name='g2g_staff')
        self.other_customer = make_user('sig_other')
        self.quote = make_sent_quote(self.customer)

    # GIVEN customer WHEN POST valid signature SHOULD create QuoteSignature with role='customer'
    def test_customer_can_sign(self):
        self.client.force_login(self.customer)
        response = self.client.post(sign_url(self.quote.pk), {'signature_image': VALID_SIG})
        self.assertIn(response.status_code, [302, 200])
        sig = QuoteSignature.objects.get(quote=self.quote, signer_role='customer')
        self.assertEqual(sig.signer, self.customer)
        self.assertEqual(sig.signature_image, VALID_SIG)

    # GIVEN staff user WHEN POST valid signature SHOULD create QuoteSignature with role='g2g_staff'
    def test_staff_can_sign(self):
        self.client.force_login(self.staff)
        response = self.client.post(sign_url(self.quote.pk), {'signature_image': VALID_SIG})
        self.assertIn(response.status_code, [302, 200])
        sig = QuoteSignature.objects.get(quote=self.quote, signer_role='g2g_staff')
        self.assertEqual(sig.signer, self.staff)

    # GIVEN customer already signed WHEN POST again SHOULD return 409
    def test_duplicate_signature_returns_409(self):
        QuoteSignature.objects.create(
            quote=self.quote, signer=self.customer,
            signer_name='Test User', signer_role='customer',
            signature_image=VALID_SIG,
        )
        self.client.force_login(self.customer)
        response = self.client.post(sign_url(self.quote.pk), {'signature_image': VALID_SIG})
        self.assertEqual(response.status_code, 409)

    # GIVEN invalid base64 string WHEN POST SHOULD return 400
    def test_invalid_signature_format_returns_400(self):
        self.client.force_login(self.customer)
        response = self.client.post(sign_url(self.quote.pk), {'signature_image': 'not-a-valid-image'})
        self.assertEqual(response.status_code, 400)

    # GIVEN empty signature_image WHEN POST SHOULD return 400
    def test_empty_signature_returns_400(self):
        self.client.force_login(self.customer)
        response = self.client.post(sign_url(self.quote.pk), {'signature_image': ''})
        self.assertEqual(response.status_code, 400)

    # GIVEN other customer WHEN POST signature SHOULD return 403
    def test_other_customer_cannot_sign(self):
        self.client.force_login(self.other_customer)
        response = self.client.post(sign_url(self.quote.pk), {'signature_image': VALID_SIG})
        self.assertEqual(response.status_code, 403)

    # GIVEN unauthenticated user WHEN POST SHOULD redirect to login
    def test_unauthenticated_redirects_to_login(self):
        response = self.client.post(sign_url(self.quote.pk), {'signature_image': VALID_SIG})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    # GIVEN draft quote WHEN customer tries to sign SHOULD return 404
    def test_customer_cannot_sign_draft_quote(self):
        self.quote.status = 'draft'
        self.quote.save(update_fields=['status', 'updated_at'])
        self.client.force_login(self.customer)
        response = self.client.post(sign_url(self.quote.pk), {'signature_image': VALID_SIG})
        self.assertEqual(response.status_code, 404)

    # GIVEN report with 2 signatures WHEN GET print view SHOULD include both in context
    def test_print_view_includes_signatures_in_context(self):
        QuoteSignature.objects.create(
            quote=self.quote, signer=self.customer, signer_name='Test User',
            signer_role='customer', signature_image=VALID_SIG,
        )
        QuoteSignature.objects.create(
            quote=self.quote, signer=self.staff, signer_name='Staff User',
            signer_role='g2g_staff', signature_image=VALID_SIG,
        )
        self.client.force_login(self.staff)
        response = self.client.get(print_url(self.quote.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['signatures']), 2)
