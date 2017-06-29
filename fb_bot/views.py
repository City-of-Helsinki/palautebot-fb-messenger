# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.views import generic
from django.http.response import HttpResponse
from django.shortcuts import render

# Create your views here.
class FbBotView(generic.View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("Hello World!")