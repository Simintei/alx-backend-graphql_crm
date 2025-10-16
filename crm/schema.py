import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
import re

from .models import Customer, Product, Order


# ----------------------------
# Types
# ----------------------------
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone", "created_at")
        interfaces = (graphene.relay.Node,)


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")
        interfaces = (graphene.relay.Node,)


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")
        interfaces = (graphene.relay.Node,)


# ----------------------------
# Queries (from previous task)
# ----------------------------
class Query(graphene.ObjectType):
    all_customers = DjangoFilterConnectionField(CustomerType, order_by=graphene.String())
    all_products = DjangoFilterConnectionField(ProductType, order_by=graphene.String())
    all_orders = DjangoFilterConnectionField(OrderType, order_by=graphene.String())

    def resolve_all_customers(self, info, **kwargs):
        qs = Customer.objects.all()
        order_by = kwargs.get('order_by')
        if order_by:
            qs = qs.order_by(order_by)
        return qs

    def resolve_all_products(self, info, **kwargs):
        qs = Product.objects.all()
        order_by = kwargs.get('order_by')
        if order_by:
            qs = qs.order_by(order_by)
        return qs

    def resolve_all_orders(self, info, **kwargs):
        qs = Order.objects.all()
        order_by = kwargs.get('order_by')
        if order_by:
            qs = qs.order_by(order_by)
        return qs


# ----------------------------
# Mutations
# ----------------------------

# --- CreateCustomer ---
class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        # Validate unique email
        if Customer.objects.filter(email=email).exists():
            raise ValidationError("Email already exists.")

        # Validate phone format
        if phone and not re.match(r"^(\+\d{9,15}|\d{3}-\d{3}-\d{4})$", phone):
            raise ValidationError("Invalid phone number format.")

        customer = Customer.objects.create(name=name, email=email, phone=phone)
        return CreateCustomer(customer=customer, message="Customer created successfully.")


# --- BulkCreateCustomers ---
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, input):
        customers = []
        errors = []

        for data in input:
            try:
                if Customer.objects.filter(email=data.email).exists():
                    errors.append(f"Email {data.email} already exists.")
                    continue
                if data.phone and not re.match(r"^(\+\d{9,15}|\d{3}-\d{3}-\d{4})$", data.phone):
                    errors.append(f"Invalid phone format for {data.name}.")
                    continue

                customer = Customer(name=data.name, email=data.email, phone=data.phone)
                customer.save()
                customers.append(customer)
            except Exception as e:
                errors.append(str(e))

        return BulkCreateCustomers(customers=customers, errors=errors)


# --- CreateProduct ---
class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=False, default_value=0)

    product = graphene.Field(ProductType)

    def mutate(self, info, name, price, stock):
        if price <= 0:
            raise ValidationError("Price must be positive.")
        if stock < 0:
            raise ValidationError("Stock cannot be negative.")

        product = Product.objects.create(name=name, price=price, stock=stock)
        return CreateProduct(product=product)


# --- CreateOrder ---
class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime(required=False)

    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_ids, order_date=None):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise ValidationError("Invalid customer ID.")

        products = Product.objects.filter(pk__in=product_ids)
        if not products.exists():
            raise ValidationError("No valid products found for provided IDs.")

        total_amount = sum(p.price for p in products)
        order_date = order_date or timezone.now()

        order = Order.objects.create(customer=customer, total_amount=total_amount, order_date=order_date)
        order.products.set(products)
        order.save()

        return CreateOrder(order=order)


# ----------------------------
# Root Mutation
# ----------------------------
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
