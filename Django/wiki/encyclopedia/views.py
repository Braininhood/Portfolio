import random
import markdown2
from django.shortcuts import render, redirect
from django import forms
from django.urls import reverse
from . import util
from django.views.decorators.csrf import csrf_protect


class NewEntryForm(forms.Form):
    title = forms.CharField(label="Title", widget=forms.TextInput(attrs={'class': 'form-control'}))
    content = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}))


class EditEntryForm(forms.Form):
    content = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}))


class PageForm(forms.Form):
    title = forms.CharField(label="Title", widget=forms.TextInput(attrs={'class': 'form-control'}))
    content = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10}))


def index(request):
    return render(request, "encyclopedia/index.html", {
        "entries": util.list_entries()
    })


def entry_page(request, title):
    content = util.get_entry(title)
    if content is None:
        return render(request, "encyclopedia/not_found.html", {"title": title})

    # Convert Markdown to HTML
    content_html = markdown2.markdown(content)

    return render(request, "encyclopedia/entry.html", {
        "title": title,
        "content": content_html
    })


def search(request):
    query = request.GET.get('q', '').strip()  # Remove spaces

    if not query:
        return redirect("index")  # Redirect if search is empty

    all_entries = util.list_entries()

    # Find articles with the search term in the title
    title_matches = [entry for entry in all_entries if query.lower() in entry.lower()]

    # Find articles with the search term inside the content (excluding title matches)
    content_matches = []
    for entry in all_entries:
        if entry not in title_matches:  # Avoid duplicates
            content = util.get_entry(entry)  # Load article content
            if content and query.lower() in content.lower():
                content_matches.append(entry)

    return render(request, "encyclopedia/search_results.html", {
        "query": query,
        "title_matches": title_matches,
        "content_matches": content_matches
    })


@csrf_protect
def new_page(request):
    if request.method == "POST":
        title = request.POST["title"]
        content = request.POST["content"]
        if util.get_entry(title):
            return render(request, "encyclopedia/new_page.html", {
                "form": PageForm(),
                "error": "Page already exists!"
            })
        util.save_entry(title, content)
        return redirect(reverse("encyclopedia:entry_page", args=[title]))
    return render(request, "encyclopedia/new_page.html", {"form": PageForm()})


@csrf_protect
def edit_page(request, title):
    if request.method == "POST":
        content = request.POST["content"]
        util.save_entry(title, content)
        return redirect("encyclopedia:entry_page", title=title)

    content = util.get_entry(title)
    return render(request, "encyclopedia/edit_page.html", {"title": title, "content": content})


def random_page(request):
    entries = util.list_entries()
    if entries:
        random_title = random.choice(entries)
        # Ensure this is correct
        return redirect(reverse('encyclopedia:entry_page', args=[random_title]))
    return render(request, "encyclopedia/error.html", {"message": "No entries available."})
