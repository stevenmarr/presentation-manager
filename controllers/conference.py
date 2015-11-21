from dateutil.parser import *

from mainh import BaseHandler
from config.forms import ConferenceForm
from helpers import admin_required
class UpdateConferenceHandler(BaseHandler):
    """ Handler for updating conferece data """
    @admin_required
    def get(self):
        """ Given the conference key, return a form with conference data """

        conference_data = self.get_conference_data()
        form = ConferenceForm(obj = conference_data)
        #form.start.data = parse(conference_data.start_date).date()
        form.start.data = ('%s'% conference_data.start_date)#.date()
        form.end.data = ('%s'% conference_data.end_date)#.date()

        return self.render_response('update_conference.html', form=form)
    def post(self):
        """ Update conference data """

        conference_data = self.get_conference_data()
        form = ConferenceForm(self.request.POST, obj = conference_data)
        if not form.validate():
            return self.render_response('update_conference.html',
                                        form=form,
                                        failed=True,
                                        message="Form failed to validate with errors %s"% form.errors)
        form.populate_obj(conference_data)
        conference_data.start_date = parse('%s'% form.start.data).date()
        conference_data.end_date = parse('%s'% form.end.data).date()
    #TODO: compare values, make sure they are in chronological order.
        conference_data.save()
        data_cache.set('%s-conference_data'% self.module, None)
        time.sleep(.25)
        return self.redirect(uri_for('update_conference'))
