# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.views import generic
from django.http.response import HttpResponse
from django.shortcuts import render

# Create your views here.
class FbBotView(generic.View):
    def get(self, request, *args, **kwargs):
        if self.request.GET['hub.verify_token'] == '123456789123456789':
            return HttpResponse(self.request.GET['hub.challenge'])
        else:
            return HttpResponse("Error, invalid token")