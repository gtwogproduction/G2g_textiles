"""
Integration tests for the G2G Textiles customer/production portal.

Roles:
  - g2g_staff group  → staff views
  - factory group    → factory views
  - no group         → customer views
"""

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User, Group
from django.core import mail
from django.urls import reverse

from homepage.models import QuoteRequest, OrderStatusUpdate, Quote, QuoteSignature


# ---------------------------------------------------------------------------
# Helpers / factories
# ---------------------------------------------------------------------------

def make_group(name):
    """Return (or create) a Django auth Group by name."""
    group, _ = Group.objects.get_or_create(name=name)
    return group


def make_user(username, password='testpass123', group_name=None):
    """Create a User, optionally adding them to a named group."""
    user = User.objects.create_user(username=username, password=password, email=f'{username}@test.com')
    if group_name:
        user.groups.add(make_group(group_name))
    return user


def make_quote(customer=None, assigned_factory=None):
    """
    Create a minimal QuoteRequest satisfying all required CharField constraints.
    Only fields without model-level defaults are supplied explicitly.
    """
    return QuoteRequest.objects.create(
        company_name='Test Co',
        industry='sports_club',
        contact_name='Jane Doe',
        role='owner',
        email='jane@test.com',
        product_types='tshirts',
        quantity_per_style='50-100',
        gender_sizing='unisex',
        print_method='screen_print',
        print_positions='1',
        design_files_status='yes_vector',
        desired_delivery='flexible',
        sample_required='no',
        budget_range='1k-5k',
        customer=customer,
        assigned_factory=assigned_factory,
    )


# ---------------------------------------------------------------------------
# URL constants (all under /en/ because of i18n_patterns)
# ---------------------------------------------------------------------------

LOGIN_URL = '/en/portal/login/'
PORTAL_HOME_URL = '/en/portal/'
CUSTOMER_DASHBOARD_URL = '/en/portal/customer/'
STAFF_DASHBOARD_URL = '/en/portal/staff/'
FACTORY_DASHBOARD_URL = '/en/portal/factory/'


def customer_order_url(pk):
    return f'/en/portal/customer/{pk}/'


def staff_order_url(pk):
    return f'/en/portal/staff/{pk}/'


def factory_order_url(pk):
    return f'/en/portal/factory/{pk}/'


def staff_create_quote_url(pk):
    return f'/en/portal/staff/{pk}/quote/create/'


def staff_quote_edit_url(quote_pk):
    return f'/en/portal/staff/quote/{quote_pk}/'


def staff_quote_send_url(quote_pk):
    return f'/en/portal/staff/quote/{quote_pk}/send/'


def customer_quote_url(pk):
    return f'/en/portal/customer/{pk}/quote/'


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PortalTestCase(TestCase):
    """Base test case that bypasses the staticfiles manifest requirement."""
    pass


class AuthRedirectTests(PortalTestCase):
    """GIVEN an unauthenticated visitor"""

    def setUp(self):
        self.client = Client()

    def test_unauthenticated_portal_home_redirects_to_login(self):
        """WHEN they hit /en/portal/ SHOULD redirect to the login page."""
        response = self.client.get(PORTAL_HOME_URL)
        self.assertRedirects(response, f'{LOGIN_URL}?next={PORTAL_HOME_URL}', fetch_redirect_response=False)

    def test_unauthenticated_customer_dashboard_redirects_to_login(self):
        """WHEN they hit /en/portal/customer/ SHOULD redirect to the login page."""
        response = self.client.get(CUSTOMER_DASHBOARD_URL)
        self.assertRedirects(response, f'{LOGIN_URL}?next={CUSTOMER_DASHBOARD_URL}', fetch_redirect_response=False)

    def test_unauthenticated_staff_dashboard_redirects_to_login(self):
        """WHEN they hit /en/portal/staff/ SHOULD redirect to the login page."""
        response = self.client.get(STAFF_DASHBOARD_URL)
        self.assertRedirects(response, f'{LOGIN_URL}?next={STAFF_DASHBOARD_URL}', fetch_redirect_response=False)


class LoginTests(PortalTestCase):
    """GIVEN the login form"""

    def setUp(self):
        self.client = Client()
        self.user = make_user('logintest')

    def test_valid_credentials_redirect_to_portal_home(self):
        """WHEN correct credentials are POSTed SHOULD redirect to portal_home."""
        response = self.client.post(LOGIN_URL, {'username': 'logintest', 'password': 'testpass123'})
        self.assertRedirects(response, PORTAL_HOME_URL, fetch_redirect_response=False)

    def test_wrong_password_re_renders_login_with_error(self):
        """WHEN wrong password is POSTed SHOULD re-render login (200) with a form error."""
        response = self.client.post(LOGIN_URL, {'username': 'logintest', 'password': 'wrongpass'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class RoleRoutingTests(PortalTestCase):
    """GIVEN portal_home WHEN a user is logged in SHOULD redirect by role."""

    def test_staff_user_redirected_to_staff_dashboard(self):
        """GIVEN a g2g_staff user SHOULD redirect to staff_dashboard."""
        staff = make_user('staffroute', group_name='g2g_staff')
        self.client.force_login(staff)
        response = self.client.get(PORTAL_HOME_URL)
        self.assertRedirects(response, STAFF_DASHBOARD_URL, fetch_redirect_response=False)

    def test_factory_user_redirected_to_factory_dashboard(self):
        """GIVEN a factory user SHOULD redirect to factory_dashboard."""
        factory = make_user('factoryroute', group_name='factory')
        self.client.force_login(factory)
        response = self.client.get(PORTAL_HOME_URL)
        self.assertRedirects(response, FACTORY_DASHBOARD_URL, fetch_redirect_response=False)

    def test_customer_user_redirected_to_customer_dashboard(self):
        """GIVEN a user with no group SHOULD redirect to customer_dashboard."""
        customer = make_user('customerroute')
        self.client.force_login(customer)
        response = self.client.get(PORTAL_HOME_URL)
        self.assertRedirects(response, CUSTOMER_DASHBOARD_URL, fetch_redirect_response=False)


class CustomerIsolationTests(PortalTestCase):
    """GIVEN a customer user WHEN viewing orders SHOULD only see their own."""

    def setUp(self):
        self.customer = make_user('customer1')
        self.other_customer = make_user('customer2')
        self.own_quote = make_quote(customer=self.customer)
        self.other_quote = make_quote(customer=self.other_customer)
        self.client.force_login(self.customer)

    def test_customer_can_view_own_order(self):
        """SHOULD return 200 for an order belonging to the logged-in customer."""
        response = self.client.get(customer_order_url(self.own_quote.pk))
        self.assertEqual(response.status_code, 200)

    def test_customer_gets_404_on_another_customers_order(self):
        """SHOULD return 404 when accessing an order owned by a different customer."""
        response = self.client.get(customer_order_url(self.other_quote.pk))
        self.assertEqual(response.status_code, 404)


class StaffAccessTests(PortalTestCase):
    """GIVEN a g2g_staff user WHEN accessing staff views SHOULD see all orders."""

    def setUp(self):
        self.staff = make_user('staffuser', group_name='g2g_staff')
        self.customer = make_user('anycustomer')
        self.quote = make_quote(customer=self.customer)
        self.client.force_login(self.staff)

    def test_staff_dashboard_returns_200(self):
        """SHOULD return 200 for the staff dashboard."""
        response = self.client.get(STAFF_DASHBOARD_URL)
        self.assertEqual(response.status_code, 200)

    def test_staff_can_view_any_order(self):
        """SHOULD return 200 for staff_order regardless of quote ownership."""
        response = self.client.get(staff_order_url(self.quote.pk))
        self.assertEqual(response.status_code, 200)


class FactoryIsolationTests(PortalTestCase):
    """GIVEN a factory user WHEN accessing factory views SHOULD only see assigned orders."""

    def setUp(self):
        self.factory = make_user('factory1', group_name='factory')
        self.other_factory = make_user('factory2', group_name='factory')
        self.assigned_quote = make_quote(assigned_factory=self.factory)
        self.assigned_quote.payment_confirmed = True
        self.assigned_quote.save(update_fields=['payment_confirmed'])
        self.unassigned_quote = make_quote(assigned_factory=self.other_factory)
        self.unassigned_quote.payment_confirmed = True
        self.unassigned_quote.save(update_fields=['payment_confirmed'])
        self.client.force_login(self.factory)

    def test_factory_gets_404_on_order_not_assigned_to_them(self):
        """SHOULD return 404 when factory_order pk is not assigned to this user."""
        response = self.client.get(factory_order_url(self.unassigned_quote.pk))
        self.assertEqual(response.status_code, 404)

    def test_factory_can_view_assigned_order(self):
        """SHOULD return 200 for an order assigned to this factory user."""
        response = self.client.get(factory_order_url(self.assigned_quote.pk))
        self.assertEqual(response.status_code, 200)


class StaffStatusUpdateTests(PortalTestCase):
    """GIVEN a g2g_staff user WHEN posting to staff_order SHOULD create an OrderStatusUpdate."""

    def setUp(self):
        self.staff = make_user('staffupdate', group_name='g2g_staff')
        self.customer = make_user('custupdate')
        self.quote = make_quote(customer=self.customer)
        self.client.force_login(self.staff)

    def test_post_update_creates_order_status_update(self):
        """WHEN post_update is submitted SHOULD create one OrderStatusUpdate for the quote."""
        payload = {
            'post_update': '1',
            'update_type': 'update',
            'status': 'in_review',
            'note': 'We are looking into your order.',
        }
        response = self.client.post(staff_order_url(self.quote.pk), payload)
        # Should redirect back to the same staff_order page after success
        self.assertRedirects(response, staff_order_url(self.quote.pk), fetch_redirect_response=False)
        self.assertEqual(OrderStatusUpdate.objects.filter(quote_request=self.quote).count(), 1)
        update = OrderStatusUpdate.objects.get(quote_request=self.quote)
        self.assertEqual(update.status, 'quote_received')  # first in pipeline
        self.assertEqual(update.created_by, self.staff)

    def test_post_issue_creates_update_with_issue_type(self):
        """WHEN post_update is submitted with update_type=issue SHOULD set update_type to issue."""
        payload = {
            'post_update': '1',
            'update_type': 'issue',
            'status': 'in_production',
            'note': 'Fabric delayed at customs.',
        }
        self.client.post(staff_order_url(self.quote.pk), payload)
        update = OrderStatusUpdate.objects.get(quote_request=self.quote)
        self.assertEqual(update.update_type, 'issue')


class StaffAssignFactoryTests(PortalTestCase):
    """GIVEN a g2g_staff user WHEN posting assign_factory SHOULD set quote.assigned_factory."""

    def setUp(self):
        self.staff = make_user('staffassign', group_name='g2g_staff')
        self.factory_user = make_user('factoryassign', group_name='factory')
        self.quote = make_quote()
        self.client.force_login(self.staff)

    def test_assign_factory_sets_assigned_factory_on_quote(self):
        """WHEN assign_factory is submitted SHOULD persist the factory user on the quote."""
        payload = {
            'assign_factory': '1',
            'factory': self.factory_user.pk,
        }
        response = self.client.post(staff_order_url(self.quote.pk), payload)
        self.assertRedirects(response, staff_order_url(self.quote.pk), fetch_redirect_response=False)
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.assigned_factory, self.factory_user)


class FactoryStatusUpdateTests(PortalTestCase):
    """GIVEN a factory user assigned to an order WHEN posting to factory_order SHOULD create an OrderStatusUpdate."""

    def setUp(self):
        self.factory = make_user('factorystatus', group_name='factory')
        self.customer = make_user('custfactory')
        self.quote = make_quote(customer=self.customer, assigned_factory=self.factory)
        self.quote.payment_confirmed = True
        self.quote.save(update_fields=['payment_confirmed'])
        self.client.force_login(self.factory)

    def test_post_creates_order_status_update(self):
        """WHEN a valid status form is POSTed SHOULD create one OrderStatusUpdate."""
        payload = {
            'update_type': 'update',
            'status': 'in_production',
            'note': 'Production started today.',
        }
        response = self.client.post(factory_order_url(self.quote.pk), payload)
        self.assertRedirects(response, factory_order_url(self.quote.pk), fetch_redirect_response=False)
        self.assertEqual(OrderStatusUpdate.objects.filter(quote_request=self.quote).count(), 1)
        update = OrderStatusUpdate.objects.get(quote_request=self.quote)
        self.assertEqual(update.status, 'quote_received')  # first in pipeline
        self.assertEqual(update.created_by, self.factory)

    def test_post_issue_creates_update_with_issue_type(self):
        """WHEN a factory posts with update_type=issue SHOULD set update_type to issue."""
        payload = {
            'update_type': 'issue',
            'status': 'in_production',
            'note': 'Machine breakdown, 3-day delay.',
        }
        self.client.post(factory_order_url(self.quote.pk), payload)
        update = OrderStatusUpdate.objects.get(quote_request=self.quote)
        self.assertEqual(update.update_type, 'issue')


class CustomerBlockedFromStaffViewsTests(PortalTestCase):
    """GIVEN a customer user (no group) WHEN hitting staff URLs SHOULD be redirected away."""

    def setUp(self):
        self.customer = make_user('custblocked')
        self.quote = make_quote(customer=self.customer)
        self.client.force_login(self.customer)

    def test_customer_cannot_access_staff_dashboard(self):
        """SHOULD redirect (not 200) when a customer GETs the staff dashboard."""
        response = self.client.get(STAFF_DASHBOARD_URL)
        # staff_dashboard redirects non-staff to portal_home, which then redirects to customer_dashboard
        self.assertIn(response.status_code, [301, 302])
        self.assertNotEqual(response.status_code, 200)

    def test_customer_cannot_access_staff_order(self):
        """SHOULD redirect (not 200) when a customer GETs a staff_order page."""
        response = self.client.get(staff_order_url(self.quote.pk))
        self.assertIn(response.status_code, [301, 302])
        self.assertNotEqual(response.status_code, 200)


class StaffBlockedFromCustomerViewsTests(PortalTestCase):
    """GIVEN a g2g_staff user WHEN hitting customer-only URLs SHOULD be redirected via portal_home."""

    def setUp(self):
        self.staff = make_user('staffblocked', group_name='g2g_staff')
        self.customer = make_user('custowner')
        self.quote = make_quote(customer=self.customer)
        self.client.force_login(self.staff)

    def test_staff_redirected_from_customer_dashboard(self):
        """SHOULD not return 200 — staff is redirected away from customer_dashboard."""
        response = self.client.get(CUSTOMER_DASHBOARD_URL)
        self.assertIn(response.status_code, [301, 302])
        self.assertNotEqual(response.status_code, 200)

    def test_staff_redirected_from_customer_order(self):
        """SHOULD not return 200 — staff is redirected away from customer_order."""
        response = self.client.get(customer_order_url(self.quote.pk))
        self.assertIn(response.status_code, [301, 302])
        self.assertNotEqual(response.status_code, 200)


class QuoteBuilderTests(PortalTestCase):
    """Tests for the Quote Builder feature."""

    def setUp(self):
        self.staff = make_user('quotestaff', group_name='g2g_staff')
        self.customer = make_user('quotecustomer')
        self.other_customer = make_user('quoteother')
        self.quote_request = make_quote(customer=self.customer)

    def _create_quote_via_post(self):
        """Helper: staff POSTs to create a quote, returns the Quote object."""
        self.client.force_login(self.staff)
        data = {
            'currency': 'CHF',
            'valid_until': '2026-12-31',
            'estimated_delivery': '',
            'notes_internal': '',
            'notes_customer': '',
            # Management form for inline formset (0 extra forms)
            'line_items-TOTAL_FORMS': '1',
            'line_items-INITIAL_FORMS': '0',
            'line_items-MIN_NUM_FORMS': '0',
            'line_items-MAX_NUM_FORMS': '1000',
            'line_items-0-description': 'Test Jersey',
            'line_items-0-quantity': '100',
            'line_items-0-unit_price': '25.00',
            'line_items-0-discount_pct': '0',
            'line_items-0-note': '',
            'line_items-0-order': '0',
            'line_items-0-DELETE': '',
        }
        self.client.post(staff_create_quote_url(self.quote_request.pk), data)
        return Quote.objects.get(quote_request=self.quote_request)

    def test_staff_can_create_quote_for_request(self):
        """WHEN staff POSTs to create quote SHOULD create Quote with auto quote_number."""
        self.client.force_login(self.staff)
        data = {
            'currency': 'CHF',
            'valid_until': '2026-12-31',
            'estimated_delivery': '',
            'notes_internal': '',
            'notes_customer': '',
            'line_items-TOTAL_FORMS': '1',
            'line_items-INITIAL_FORMS': '0',
            'line_items-MIN_NUM_FORMS': '0',
            'line_items-MAX_NUM_FORMS': '1000',
            'line_items-0-description': 'Test Jersey',
            'line_items-0-quantity': '100',
            'line_items-0-unit_price': '25.00',
            'line_items-0-discount_pct': '0',
            'line_items-0-note': '',
            'line_items-0-order': '0',
            'line_items-0-DELETE': '',
        }
        self.client.post(staff_create_quote_url(self.quote_request.pk), data)
        self.assertTrue(Quote.objects.filter(quote_request=self.quote_request).exists())
        quote = Quote.objects.get(quote_request=self.quote_request)
        self.assertTrue(quote.quote_number.startswith('Q-'))

    def test_send_quote_changes_status_to_sent(self):
        """WHEN staff POSTs to send quote SHOULD change status to sent."""
        quote = self._create_quote_via_post()
        self.client.force_login(self.staff)
        self.client.post(staff_quote_send_url(quote.pk))
        quote.refresh_from_db()
        self.assertEqual(quote.status, 'sent')

    def test_customer_can_view_sent_quote(self):
        """WHEN customer GETs sent quote SHOULD return 200."""
        quote = self._create_quote_via_post()
        quote.status = 'sent'
        quote.save(update_fields=['status', 'updated_at'])
        self.client.force_login(self.customer)
        response = self.client.get(customer_quote_url(self.quote_request.pk))
        self.assertEqual(response.status_code, 200)

    def test_customer_cannot_view_draft_quote(self):
        """WHEN customer GETs draft quote SHOULD return 404."""
        self._create_quote_via_post()
        self.client.force_login(self.customer)
        response = self.client.get(customer_quote_url(self.quote_request.pk))
        self.assertEqual(response.status_code, 404)

    def test_other_customer_cannot_view_quote(self):
        """WHEN wrong customer GETs quote SHOULD return 404."""
        quote = self._create_quote_via_post()
        quote.status = 'sent'
        quote.save(update_fields=['status', 'updated_at'])
        self.client.force_login(self.other_customer)
        response = self.client.get(customer_quote_url(self.quote_request.pk))
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# Signature data shared across signing tests
# ---------------------------------------------------------------------------

SIGNATURE_PAYLOAD = {'signature_image': 'data:image/png;base64,abc123'}


def quote_sign_url(quote_pk):
    return f'/en/portal/quote/{quote_pk}/sign/'


@override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
    QUOTE_NOTIFICATION_EMAIL='staff@g2gtextiles.test',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class QuoteSigningTests(PortalTestCase):
    """Tests for the quote_sign view — customer and staff signing behaviour."""

    def setUp(self):
        self.staff = make_user('signstaff', group_name='g2g_staff')
        self.customer = make_user('signcustomer')
        self.quote_request = make_quote(customer=self.customer)
        # Build a Quote directly (bypass the full staff create flow)
        self.quote = Quote.objects.create(
            quote_request=self.quote_request,
            status='sent',
            currency='CHF',
            created_by=self.staff,
        )

    # ------------------------------------------------------------------
    # 1. Customer signing — happy path
    # ------------------------------------------------------------------

    def test_customer_sign_sets_status_to_accepted(self):
        """
        GIVEN a sent quote
        WHEN the customer POSTs a valid signature
        SHOULD set quote.status to 'accepted'.
        """
        self.client.force_login(self.customer)
        self.client.post(quote_sign_url(self.quote.pk), SIGNATURE_PAYLOAD)
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.status, 'accepted')

    # ------------------------------------------------------------------
    # 2. Email notification after customer signing
    # ------------------------------------------------------------------

    def test_customer_sign_sends_notification_email(self):
        """
        GIVEN a sent quote
        WHEN the customer signs
        SHOULD send an email to settings.QUOTE_NOTIFICATION_EMAIL.
        """
        self.client.force_login(self.customer)
        self.client.post(quote_sign_url(self.quote.pk), SIGNATURE_PAYLOAD)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('staff@g2gtextiles.test', mail.outbox[0].to)

    # ------------------------------------------------------------------
    # 3. Staff signing — status must NOT change
    # ------------------------------------------------------------------

    def test_staff_sign_does_not_change_status(self):
        """
        GIVEN a sent quote
        WHEN staff POSTs a valid signature
        SHOULD NOT change quote.status (remains 'sent').
        """
        self.client.force_login(self.staff)
        self.client.post(quote_sign_url(self.quote.pk), SIGNATURE_PAYLOAD)
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.status, 'sent')

    # ------------------------------------------------------------------
    # 4. Duplicate signing — idempotency guard
    # ------------------------------------------------------------------

    def test_customer_sign_twice_returns_409(self):
        """
        GIVEN a quote already accepted (customer already signed)
        WHEN the customer attempts to sign again
        SHOULD return 409.
        """
        self.quote.status = 'accepted'
        self.quote.save(update_fields=['status'])
        QuoteSignature.objects.create(
            quote=self.quote,
            signer=self.customer,
            signer_name='Test Customer',
            signer_role=QuoteSignature.ROLE_CUSTOMER,
            signature_image='data:image/png;base64,abc123',
        )
        self.client.force_login(self.customer)
        response = self.client.post(quote_sign_url(self.quote.pk), SIGNATURE_PAYLOAD)
        self.assertEqual(response.status_code, 409)

    # ------------------------------------------------------------------
    # 5. Draft quote — must not be signable
    # ------------------------------------------------------------------

    def test_customer_sign_draft_quote_returns_404(self):
        """
        GIVEN a draft quote (not yet sent to the customer)
        WHEN the customer tries to sign it
        SHOULD return 404.
        """
        self.quote.status = 'draft'
        self.quote.save(update_fields=['status'])
        self.client.force_login(self.customer)
        response = self.client.post(quote_sign_url(self.quote.pk), SIGNATURE_PAYLOAD)
        self.assertEqual(response.status_code, 404)


def customer_quote_print_url(pk):
    return reverse('customer_quote_print', kwargs={'pk': pk})


class CustomerQuotePrintTests(PortalTestCase):
    """Tests for the customer_quote_print view."""

    def setUp(self):
        self.staff = make_user('printstaff', group_name='g2g_staff')
        self.customer = make_user('printcustomer')
        self.other_customer = make_user('printother')
        self.quote_request = make_quote(customer=self.customer)

    def test_customer_with_sent_quote_gets_200(self):
        """
        GIVEN a customer with a sent quote
        WHEN GET customer_quote_print
        SHOULD return 200.
        """
        Quote.objects.create(
            quote_request=self.quote_request,
            status='sent',
            currency='CHF',
            quote_number='Q-2026-0001',
            created_by=self.staff,
        )
        self.client.force_login(self.customer)
        response = self.client.get(customer_quote_print_url(self.quote_request.pk))
        self.assertEqual(response.status_code, 200)

    def test_other_customer_gets_404(self):
        """
        GIVEN another customer (different account)
        WHEN GET customer_quote_print for a different customer's order
        SHOULD return 404.
        """
        Quote.objects.create(
            quote_request=self.quote_request,
            status='sent',
            currency='CHF',
            quote_number='Q-2026-0002',
            created_by=self.staff,
        )
        self.client.force_login(self.other_customer)
        response = self.client.get(customer_quote_print_url(self.quote_request.pk))
        self.assertEqual(response.status_code, 404)

    def test_staff_user_is_redirected(self):
        """
        GIVEN a staff user (g2g_staff group)
        WHEN GET customer_quote_print
        SHOULD redirect — staff are not customers, not 200.
        """
        Quote.objects.create(
            quote_request=self.quote_request,
            status='sent',
            currency='CHF',
            quote_number='Q-2026-0003',
            created_by=self.staff,
        )
        self.client.force_login(self.staff)
        response = self.client.get(customer_quote_print_url(self.quote_request.pk))
        self.assertIn(response.status_code, [301, 302])
        self.assertNotEqual(response.status_code, 200)

    def test_customer_with_draft_quote_gets_404(self):
        """
        GIVEN a customer with a draft quote (not yet sent)
        WHEN GET customer_quote_print
        SHOULD return 404.
        """
        Quote.objects.create(
            quote_request=self.quote_request,
            status='draft',
            currency='CHF',
            quote_number='Q-2026-0004',
            created_by=self.staff,
        )
        self.client.force_login(self.customer)
        response = self.client.get(customer_quote_print_url(self.quote_request.pk))
        self.assertEqual(response.status_code, 404)

    def test_customer_with_no_quote_gets_404(self):
        """
        GIVEN a customer whose order has no Quote attached
        WHEN GET customer_quote_print
        SHOULD return 404.
        """
        self.client.force_login(self.customer)
        response = self.client.get(customer_quote_print_url(self.quote_request.pk))
        self.assertEqual(response.status_code, 404)
