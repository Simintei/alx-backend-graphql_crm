import graphene

class Query(CRMQuery, graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")

class Mutation(CRMMutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query)

