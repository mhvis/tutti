import os.path
from collections import namedtuple
from datetime import date

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.templatetags.static import static
from django.views.generic import TemplateView

LinkCard = namedtuple('LinkCard', ['icon', 'link', 'text', 'new_tab'])
SubAssociationCard = namedtuple('SubAssociationCard', ['img', 'link', 'text', 'new_tab'])


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Create urls
        context.update({
            'link_cards': [
                LinkCard(icon='info',
                         link='https://esmgquadrivium.sharepoint.com/SitePages/Home.aspx',
                         text="Members info (SharePoint)",
                         new_tab=True),
                LinkCard(icon='camera',
                         link='https://esmgquadrivium.sharepoint.com/Pictures/Forms/Thumbnails.aspx',
                         text="Pictures (SharePoint)",
                         new_tab=True),
                LinkCard(icon='file',
                         link='https://esmgquadrivium.sharepoint.com/DoQumenten/Forms/AllItems.aspx',
                         text="Presstos, audio recordings, GMM documents (SharePoint)",
                         new_tab=True),
                LinkCard(icon='utensils',
                         link='https://dining.studentencultuur.nl/',
                         text="Scala Dining",
                         new_tab=True),
                LinkCard(icon='calendar',
                         link='https://deplint.nu/',
                         text="Rehearsal room bookings",
                         new_tab=True),
                False,  # Invisible card
            ],
            'sub_association_cards': [
                SubAssociationCard(img=static('img/subassociations/auletes.jpg'),
                                   link='https://esmgquadrivium.sharepoint.com/auletes/SitePages/Home.aspx',
                                   text="Auletes",
                                   new_tab=True),
                SubAssociationCard(img=static('img/subassociations/ensuite.jpg'),
                                   link='https://esmgquadrivium.sharepoint.com/ensuite/SitePages/Home.aspx',
                                   text="Ensuite",
                                   new_tab=True),
                SubAssociationCard(img=static('img/subassociations/vokollage.jpg'),
                                   link='https://esmgquadrivium.sharepoint.com/vokollage/SitePages/Home.aspx',
                                   text="Vokollage",
                                   new_tab=True),
                SubAssociationCard(img=static('img/subassociations/ensembles.jpg'),
                                   link='https://esmgquadrivium.sharepoint.com/ensembles/SitePages/Home.aspx',
                                   text="Ensembles and piano members",
                                   new_tab=True),
            ],
        })
        return context


class AboutView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/about.html'

    def get_context_data(self, **kwargs):
        """Loads app build date from file."""
        context = super().get_context_data(**kwargs)
        build_date = None
        try:
            with open(os.path.join(settings.BASE_DIR, "builddate.txt")) as f:
                build_date = date.fromisoformat(f.read().strip())
        except FileNotFoundError:
            pass
        context['build_date'] = build_date
        return context
