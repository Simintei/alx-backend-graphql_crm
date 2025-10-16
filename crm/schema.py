import graphene
from graphene_django import DjangoObjectType
from django.core.validators import RegexValidator
from django.db import transaction
from django.utils import timezone
from .models import Customer, Product, Order

# ==============================
#  GraphQL Types
# ==============================
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")


class Query(graphene.ObjectType):
    all_customers = graphene.List(CustomerType)

    def resolve_all_customers(root, info):
        return Customer.objects.all()


# ==============================
#  MUTATIONS
# ==============================
class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        # Email uniqueness validation
        if Customer.objects.filter(email=email).exists():
            raise Exception("Email already exists")

        # Phone validation (optional)
        if phone:
            validator = RegexValidator(
                regex=r'^\+?\d{1,3}?[-.\s]?\d{3,}$',
                message="Invalid phone format. Use +1234567890 or 123-456-7890"
            )
            validator(phone)

        customer = Customer.objects.create(name=name, email=email, phone=phone)
        return CreateCustomer(customer=customer, message="Customer created successfully.")


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(
            graphene.InputObjectType(
                name="BulkCustomerInput",
                fields={
                    "name": graphene.String(required=True),
                    "email": graphene.String(required=True),
                    "phone": graphene.String(required=False),
                },
            )
        )

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, input):
        customers = []
        errors = []
        for data in input:
            try:
                if Customer.objects.filter(email=data["email"]).exists():
                    raise Exception(f"Email {data['email']} already exists")

                customer = Customer.objects.create(
                    name=data["name"],
                    email=data["email"],
                    phone=data.get("phone", None)
                )
                customers.append(customer)
            except Exception as e:
                errors.append(str(e))
                continue
        return BulkCreateCustomers(customers=customers, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=False)

    product = graphene.Field(ProductType)

    def mutate(self, info, name, price, stock=0):
        if price <= 0:
            raise Exception("Price must be positive")
        if stock < 0:
            raise Exception("Stock cannot be negative")

        product = Product.objects.create(name=name, price=price, stock=stock)
        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime(required=False)

    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_ids, order_date=None):
        if not product_ids:
            raise Exception("At least one product must be selected")

        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID")

        products = Product.objects.filter(pk__in=product_ids)
        if not products.exists():
            raise Exception("Invalid product IDs")

        total_amount = sum([float(p.price) for p in products])
        order = Order.objects.create(
            customer=customer,
            total_amount=total_amount,
            order_date=order_date or timezone.now()
        )
        order.products.set(products)
        return CreateOrder(order=order)


# ==============================
#  QUERY + MUTATION ROOT
# ==============================
class CRMQuery(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

    def resolve_customers(self, info):
        return Customer.objects.all()

    def resolve_products(self, info):
        return Product.objects.all()

    def resolve_orders(self, info):
        return Order.objects.select_related("customer").prefetch_related("products")


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
