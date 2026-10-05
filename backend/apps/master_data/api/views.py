from rest_framework import serializers, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .registry import RESOURCES


class ValidatedSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        instance = self.Meta.model()
        if self.instance:
            for field in self.Meta.model._meta.concrete_fields:
                setattr(instance, field.attname, getattr(self.instance, field.attname))
            instance._state.adding = False
        for key, value in attrs.items():
            setattr(instance, key, value)
        instance.full_clean()
        return attrs


def serializer_for(model):
    return type(
        model.__name__ + "Serializer",
        (ValidatedSerializer,),
        {"Meta": type("Meta", (), {"model": model, "fields": "__all__"})},
    )


def viewset_for(model):
    return type(
        model.__name__ + "ViewSet",
        (viewsets.ModelViewSet,),
        {
            "queryset": model.objects.all().order_by("pk"),
            "serializer_class": serializer_for(model),
        },
    )


@api_view(["GET"])
def schema(request):
    result = {}
    for name, model in RESOURCES.items():
        fields = []
        for f in model._meta.fields:
            if f.primary_key:
                continue
            fields.append(
                {
                    "name": f.name,
                    "type": f.get_internal_type(),
                    "required": not f.blank and not f.has_default(),
                    "choices": list(f.choices or []),
                    "relation": next(
                        (
                            key
                            for key, value in RESOURCES.items()
                            if f.is_relation and value == f.related_model
                        ),
                        None,
                    ),
                }
            )
        result[name] = fields
    return Response(result)
