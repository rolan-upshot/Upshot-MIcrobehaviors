from django.http import HttpRequest, JsonResponse, HttpResponseBadRequest
from typing import Union
from upshot.models import User


def test(request: HttpRequest) -> Union[JsonResponse, HttpResponseBadRequest]:
    users = User.objects.all()
    results = []
    for u in users:
        obj = {"id": u.id, "name": u.name}
        results.append(obj)
    return JsonResponse({"status": "ok", "results": results})
