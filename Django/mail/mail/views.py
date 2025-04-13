import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.db import models
import re
from django.core.mail import EmailMessage

from .models import User, Email


def index(request):

    # Authenticated users view their inbox
    if request.user.is_authenticated:
        return render(request, "mail/inbox.html")

    # Everyone else is prompted to sign in
    else:
        return HttpResponseRedirect(reverse("login"))


# Add a helper function for email validation
def is_valid_email(email):
    # Regular expression for validating email format
    email_pattern = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    return bool(email_pattern.match(email))


@csrf_exempt
@login_required
def compose(request):
    # Composing a new email must be via POST
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    # Parse the data
    data = json.loads(request.body)
    is_draft = data.get("is_draft", False)
    
    # For drafts, we don't need recipients validation
    if not is_draft:
        # Check recipient emails
        emails = [email.strip() for email in data.get("recipients", "").split(",")]
        if emails == [""] or not emails:
            return JsonResponse({
                "error": "At least one recipient required."
            }, status=400)

        # Validate email format first
        invalid_format = [email for email in emails if email and not is_valid_email(email)]
        if invalid_format:
            return JsonResponse({
                "error": f"Invalid email format: {', '.join(invalid_format)}"
            }, status=400)

        # Convert email addresses to users
        recipients = []
        non_existent = []
        for email in emails:
            try:
                user = User.objects.get(email=email)
                recipients.append(user)
            except User.DoesNotExist:
                non_existent.append(email)
        
        if non_existent:
            return JsonResponse({
                "error": f"User(s) not found: {', '.join(non_existent)}"
            }, status=400)
    else:
        # For drafts, we'll store the recipients as is, even if they don't exist yet
        emails = [email.strip() for email in data.get("recipients", "").split(",") if email.strip()]
        recipients = []
        
        for email in emails:
            try:
                user = User.objects.get(email=email)
                recipients.append(user)
            except User.DoesNotExist:
                # For drafts, we simply skip invalid recipients
                pass

    # Get contents of email
    subject = data.get("subject", "")
    body = data.get("body", "")

    # Create email for sender (their sent folder)
    sender_email = Email(
        user=request.user,
        sender=request.user,
        subject=subject,
        body=body,
        read=True,  # Own emails are always read
        is_draft=is_draft
    )
    sender_email.save()
    
    # Add recipients to sender's copy
    for recipient in recipients:
        sender_email.recipients.add(recipient)
    sender_email.save()

    # If this is not a draft, create a copy for each recipient
    if not is_draft:
        for recipient in recipients:
            # Create a copy for recipient (their inbox)
            recipient_email = Email(
                user=recipient,  # This is the key change - set user to recipient
                sender=request.user,
                subject=subject,
                body=body,
                read=False,  # Emails received are unread by default
                is_draft=False
            )
            recipient_email.save()
            
            # Add all recipients to this email too
            for r in recipients:
                recipient_email.recipients.add(r)
            recipient_email.save()

    # If this is a reply, use the Reply-To header
    if data.get("in_reply_to"):
        # Get original email
        original_email = Email.objects.get(id=data.get("in_reply_to"))
        email_message = EmailMessage(
            subject=data["subject"],
            body=data["body"],
            from_email=request.user.email,
            to=[recipient.email for recipient in recipients],
            reply_to=[original_email.sender.email],
        )
        # Send the email...

    return JsonResponse({"message": "Email sent successfully.", "id": sender_email.id}, status=201)


@login_required
def mailbox(request, mailbox):
    # Filter emails returned based on mailbox
    if mailbox == "inbox":
        emails = Email.objects.filter(
            user=request.user, recipients=request.user, archived=False, is_draft=False
        )
    elif mailbox == "sent":
        emails = Email.objects.filter(
            user=request.user, sender=request.user, archived=False, is_draft=False
        )
    elif mailbox == "drafts":
        emails = Email.objects.filter(
            user=request.user, sender=request.user, is_draft=True
        )
    elif mailbox == "archive":
        # Include both received emails and sent emails that are archived
        emails = Email.objects.filter(
            user=request.user, archived=True, is_draft=False
        ).filter(
            models.Q(recipients=request.user) | models.Q(sender=request.user)
        ).distinct()
    else:
        return JsonResponse({"error": "Invalid mailbox."}, status=400)

    # Return emails in reverse chronological order
    emails = emails.order_by("-timestamp").all()
    return JsonResponse([email.serialize() for email in emails], safe=False)


@csrf_exempt
@login_required
def email(request, email_id):
    # Query for requested email
    try:
        email = Email.objects.get(user=request.user, pk=email_id)
    except Email.DoesNotExist:
        return JsonResponse({"error": "Email not found."}, status=404)

    # Return email contents
    if request.method == "GET":
        return JsonResponse(email.serialize())

    # Update whether email is read, archived, etc.
    elif request.method == "PUT":
        data = json.loads(request.body)
        
        # Update draft content
        if email.is_draft and data.get("is_draft", True):
            email.subject = data.get("subject", email.subject)
            email.body = data.get("body", email.body)
            
            # Update recipients
            if "recipients" in data:
                # Clear existing recipients
                email.recipients.clear()
                
                # Add new recipients
                emails = [email.strip() for email in data.get("recipients").split(",") if email.strip()]
                for recipient_email in emails:
                    try:
                        user = User.objects.get(email=recipient_email)
                        email.recipients.add(user)
                    except User.DoesNotExist:
                        # For drafts, we simply skip invalid recipients
                        pass
        
        # Update read status
        if "read" in data:
            email.read = data["read"]
            
        # Update archived status
        if "archived" in data:
            email.archived = data["archived"]
            
        email.save()
        return JsonResponse(email.serialize())

    # Delete email (for drafts)
    elif request.method == "DELETE":
        if email.is_draft:
            email.delete()
            return JsonResponse({"message": "Draft deleted successfully."}, status=200)
        else:
            return JsonResponse({"error": "Only drafts can be deleted."}, status=403)

    # Email must be via GET, PUT or DELETE
    else:
        return JsonResponse({
            "error": "GET, PUT or DELETE request required."
        }, status=400)


def login_view(request):
    if request.method == "POST":
        # Attempt to sign user in
        email = request.POST["email"]
        password = request.POST["password"]
        
        # Validate email format
        if not is_valid_email(email):
            return render(request, "mail/login.html", {
                "message": "Invalid email format."
            })
        
        # Check if the user exists
        if not User.objects.filter(email=email).exists():
            # Redirect to the registration page if the user does not exist
            return HttpResponseRedirect(reverse("register"))

        # Attempt to sign user in
        user = authenticate(request, username=email, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "mail/login.html", {
                "message": "Invalid email and/or password."
            })
    else:
        return render(request, "mail/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        email = request.POST["email"]
        
        # Validate email format
        if not is_valid_email(email):
            return render(request, "mail/register.html", {
                "message": "Invalid email format."
            })
        
        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "mail/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(email, email, password)
            user.save()
        except IntegrityError as e:
            print(e)
            return render(request, "mail/register.html", {
                "message": "Email address already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "mail/register.html")


@csrf_exempt
def api_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username', '')
            password = data.get('password', '')
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                return JsonResponse({
                    'success': True, 
                    'message': 'Login successful',
                    'user': username
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'message': 'Invalid credentials'
                }, status=401)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False, 
                'message': 'Invalid JSON format'
            }, status=400)
    
    return JsonResponse({
        'success': False, 
        'message': 'Method not allowed'
    }, status=405)
