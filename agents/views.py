import random
from django.http import HttpResponse
from django.shortcuts import render, reverse
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from leads.models import Agent, UserProfile
from .forms import AgentForm
from .mixins import OrganiserAndLoginRequiredMixin



class AgentsListView(OrganiserAndLoginRequiredMixin, generic.ListView):
    template_name = "agents/agent_list.html"
    context_object_name = "agents"

    def get_queryset(self):
        return Agent.objects.filter(organisation=self.request.user.userprofile)


class AgentCreateView(OrganiserAndLoginRequiredMixin, generic.CreateView):
    template_name = "agents/agent_create.html"
    queryset = Agent.objects.all()
    form_class = AgentForm

    def get_success_url(self):
        return reverse('agents:agent_list')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_agent = True
        user.is_organiser = False
        user.set_password(f"{random.randint(0, 1000000)}")
        user.save()
        Agent.objects.create(
            user = user,
            organisation = self.request.user.userprofile
        )

        send_mail(
            subject="You are invited to be an agent",
            message="You were added as an agent on CRM. Kindly login to start working.",
            from_email="admin@test.com",
            recipient_list=[user.email],
        )
        
        return super(AgentCreateView, self).form_valid(form)
    
    
class AgentDetailView(OrganiserAndLoginRequiredMixin, generic.DetailView):
    template_name = "agents/agent_detail.html"
    form_class = AgentForm

    def get_queryset(self):
        return Agent.objects.filter(organisation=self.request.user.userprofile)


class AgentUpdateView(OrganiserAndLoginRequiredMixin, generic.UpdateView):
    template_name = "agents/agent_update.html"
    form_class = AgentForm

    def get_queryset(self):
        user = self.request.user
        return Agent.objects.filter(organisation=user.userprofile)

    def get_success_url(self):
        return reverse('agents:agent_detail', kwargs={"pk": self.get_object().id})
    
    
class AgentDeleteView(OrganiserAndLoginRequiredMixin, generic.DeleteView):
    template_name = "agents/agent_delete.html"

    def get_queryset(self):
        return Agent.objects.filter(organisation=self.request.user.userprofile)

    def get_success_url(self):
        return reverse('agents:agent_list')
