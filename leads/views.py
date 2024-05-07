from typing import Any
from django.db.models import Count
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.contrib.auth import logout
from django.views import generic
from .models import Lead, Category
from .forms import LeadForm, CustomUserForm, AssignAgentForm, LeadCategoryUpdateForm
from agents.mixins import OrganiserAndLoginRequiredMixin

# Create your views here.

def custom_logout(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect('login')


class SignupView(generic.CreateView):
    template_name = "registration/signup.html"
    form_class = CustomUserForm

    def get_success_url(self):
        return reverse("login")


class LandingPageView(generic.TemplateView):
    template_name = "landing.html"

def landing_page(request):
    return render(request, "landing.html")


class LeadListView(LoginRequiredMixin, generic.ListView):
    template_name = "leads/lead_list.html"
    context_object_name = "leads"

    def get_queryset(self):
        user = self.request.user
        if user.is_organiser:
            querySet = Lead.objects.filter(
                organisation=user.userprofile,
                agent__isnull=False
            )
        else:
            querySet = Lead.objects.filter(
                organisation=user.agent.organisation, 
                agent__isnull=False
            )
            querySet = querySet.filter(agent__user=user)
        return querySet
    
    def get_context_data(self, **kwargs):
        context = super(LeadListView, self).get_context_data(**kwargs)
        user = self.request.user
        if user.is_organiser:
            querySet = Lead.objects.filter(
                organisation=user.userprofile, 
                agent__isnull=True
            )
            context.update({
                "unassigned_leads": querySet
            })
        return context

def lead_list(request):
    leads = Lead.objects.all()
    context = {
        "leads": leads
    }
    return render(request, "leads/lead_list.html", context)


class LeadDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = "leads/lead_detail.html"
    context_object_name = "lead"

    def get_queryset(self):
        user = self.request.user
        if user.is_organiser:
            querySet = Lead.objects.filter(organisation=user.userprofile)
        else:
            querySet = Lead.objects.filter(organisation=user.agent.organisation)
            querySet = querySet.filter(agent__user=user)
        return querySet

def lead_detail(request, pk):
    lead = Lead.objects.get(id=pk)
    context = {
        "lead": lead
    }
    return render(request, "leads/lead_detail.html", context)


class LeadCreateView(OrganiserAndLoginRequiredMixin, generic.CreateView):
    template_name = "leads/lead_create.html"
    form_class = LeadForm

    def get_success_url(self):
        return reverse("leads:lead_list")
    
    def form_valid(self, form):
        lead = form.save(commit=False)
        lead.organisation = self.request.user.userprofile
        lead.save()
        send_mail(
            subject="A lead has been created", 
            message="Go to the site to see the new lead",
            from_email="test@test.com",
            recipient_list=["test2@test.com"] 
        )
        return super(LeadCreateView, self).form_valid(form)

def create(request):
    form = LeadForm()
    if request.method == "POST":
        form = LeadForm(request.POST)
        if form.is_valid():
            form.save()            
            return redirect('/leads')
    context = {
        "form": form
    }
    return render(request, "leads/lead_create.html", context)


class LeadUpdateView(OrganiserAndLoginRequiredMixin, generic.UpdateView):
    template_name = "leads/lead_update.html"
    form_class = LeadForm

    def get_queryset(self):
        user = self.request.user
        querySet = Lead.objects.filter(organisation=user.userprofile)
        return querySet

    def get_success_url(self):
        return reverse("leads:lead_detail", kwargs={"pk": self.get_object().id})

def lead_update(request, pk):
    lead = Lead.objects.get(id=pk)
    form = LeadForm(instance=lead)
    if request.method == "POST":
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            return redirect(f'/leads/{pk}/')

    context = {
        "form": form,
        "lead": lead
    }
    return render(request, "leads/lead_update.html", context)


class LeadDeleteView(OrganiserAndLoginRequiredMixin, generic.DeleteView):
    template_name = "leads/lead_delete.html"

    def get_queryset(self):
        user = self.request.user
        querySet = Lead.objects.filter(organisation=user.userprofile)
        return querySet
    
    def get_success_url(self):
        return reverse("leads:lead_list")

def lead_delete(request, pk):
    lead = Lead.objects.get(id=pk)
    lead.delete()
    return redirect('/leads/')


class AssignAgentView(OrganiserAndLoginRequiredMixin, generic.FormView):
    template_name = "leads/assign_agent.html"
    form_class = AssignAgentForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(AssignAgentView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request": self.request
        })
        return kwargs

    def get_success_url(self):
        return reverse("leads:lead_list")
    
    def form_valid(self, form):
        agent = form.cleaned_data["agent"]
        lead = Lead.objects.get(id=self.kwargs["pk"])
        lead.agent = agent
        lead.save()
        return super(AssignAgentView, self).form_valid(form)


class UnassignedListView(LoginRequiredMixin, generic.ListView):
    template_name = "leads/unassigned_list.html"
    context_object_name = "unassigned_list"

    def get_queryset(self):
        user = self.request.user
        if user.is_organiser:
            querySet = Lead.objects.filter(
                organisation=user.userprofile
            )
        else:
            querySet = Lead.objects.filter(
                organisation=user.agent.organisation
            )
        querySet = querySet.filter(category__isnull=True)
        return querySet
        

class CategoryListView(LoginRequiredMixin, generic.ListView):
    template_name = "leads/category_list.html"
    context_object_name = "category_list"

    def get_context_data(self, **kwargs):
        user = self.request.user
        if user.is_organiser:
            querySet = Lead.objects.filter(
                organisation=user.userprofile
            )
        else:
            querySet = Lead.objects.filter(
                organisation=user.agent.organisation
            )
        context = super(CategoryListView, self).get_context_data(**kwargs)
        context.update({
            "unassigned_lead_count": querySet.filter(category__isnull=True).count()
        })
        return context

    def get_queryset(self):
        user = self.request.user
        if user.is_organiser:
            queryset = Category.objects.filter(
                organisation=user.userprofile
            )
        else:
            queryset = Category.objects.filter(
                organisation=user.agent.organisation
            )
            
        queryset = queryset.annotate(leads_count=Count('leads'))
        return queryset
    
    # def get_queryset(self):
    #     user = self.request.user
    #     if user.is_organiser:
    #         queryset = Category.objects.filter(organisation=user.userprofile).annotate(
    #             lead_count=Count('leads', filter=Q(lead__organisation=user.userprofile))
    #         )
    #     else:
    #         queryset = Category.objects.filter(organisation=user.agent.organisation).annotate(
    #             lead_count=Count('leads', filter=Q(lead__agent__user=user) & Q(lead__organisation=user.agent.organisation))
    #         )
    #     return queryset
    

class UnassignedDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = "leads/unassigned_detail.html"
    context_object_name = "unassigned_lead"

    def get_queryset(self):
        user = self.request.user
        if user.is_organiser:
            querySet = Lead.objects.filter(
                organisation=user.userprofile
            )
        else:
            querySet = Lead.objects.filter(
                organisation=user.agent.organisation
            )
            querySet = querySet.filter(category__isnull=True)
        return querySet
    

class CategoryDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = "leads/category_detail.html"
    context_object_name = "category"

    def get_queryset(self):
        user = self.request.user
        if user.is_organiser:
            querySet = Category.objects.filter(
                organisation=user.userprofile
            )
        else:
            querySet = Category.objects.filter(
                organisation=user.agent.organisation
            )
        return querySet
    

class LeadCategoryUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = "leads/lead_category_update.html"
    form_class = LeadCategoryUpdateForm

    def get_queryset(self):
        user = self.request.user
        if user.is_organiser:
            querySet = Lead.objects.filter(
                organisation=user.userprofile
            )
        else:
            querySet = Lead.objects.filter(
                organisation=user.agent.organisation
            )
        return querySet

    def get_success_url(self):
        return reverse("leads:lead_detail", kwargs={"pk": self.get_object().id}) 
