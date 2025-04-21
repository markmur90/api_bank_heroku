from django.shortcuts import render, redirect
from core.payments.models import ErrorResponse, Message, TransactionStatus, StatusResponse
from .forms import ErrorResponseForm, MessageForm, TransactionStatusForm, StatusResponseForm

def error_response_view(request):
    if request.method == 'POST':
        form = ErrorResponseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('error_response')
    else:
        form = ErrorResponseForm()
    errors = ErrorResponse.objects.all()
    return render(request, 'complementary/error_response.html', {'form': form, 'errors': errors})

def message_view(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('message')
    else:
        form = MessageForm()
    messages = Message.objects.all()
    return render(request, 'complementary/message.html', {'form': form, 'messages': messages})

def transaction_status_view(request):
    if request.method == 'POST':
        form = TransactionStatusForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('transaction_status')
    else:
        form = TransactionStatusForm()
    statuses = TransactionStatus.objects.all()
    return render(request, 'complementary/transaction_status.html', {'form': form, 'statuses': statuses})

def status_response_view(request):
    if request.method == 'POST':
        form = StatusResponseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('status_response')
    else:
        form = StatusResponseForm()
    statuses = StatusResponse.objects.all()
    return render(request, 'complementary/status_response.html', {'form': form, 'statuses': statuses})
