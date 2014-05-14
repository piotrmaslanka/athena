from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'athena.front.index.index'),
    url(r'^about/$', 'athena.front.index.about'),
    url(r'^register/$', 'athena.users.views.register'),
    url(r'^logout/$', 'athena.users.views.logout'),
    url(r'^admin-login/$', 'athena.radmin.login_view.login'),
    url(r'^profile/$', 'athena.users.views.profile'),
    url(r'^login/$', 'athena.users.views.login'),
    url(r'^login/demo/$', 'athena.users.views.demo'),

    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'D:/projects/athena/media/'}),  
    (r'^uploads/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'D:/projects/athena/uploads/'}),  
)

urlpatterns += patterns('athena.rstudent',
    url(r'^demo/start/(?P<test_id>\d+)/$', 'demo.start_demo_exam'),
    url(r'^past/$', 'protocol.index'),
    url(r'^past/(?P<protocol_id>\d+)/$', 'protocol.index'),
    url(r'^groups/$', 'views.groups'),
    url(r'^groups/join/$', 'views.join_group'),    
)

urlpatterns += patterns('athena.tests',
    url(r'^test/ajax/$', 'views.ajax'),
    url(r'^test/$', 'views.test'),
)

urlpatterns += patterns('athena.rteacher',

    url(r'^teacher/groups/$', 'manage_groups.list'),
    url(r'^teacher/groups/(?P<group_id>\d+)/$', 'manage_groups.group'),
    url(r'^teacher/groups/(?P<group_id>\d+)/members/$', 'manage_groups.members'),
    url(r'^teacher/groups/(?P<group_id>\d+)/requests/$', 'manage_groups.requests'),
    url(r'^teacher/groups/create/$', 'manage_groups.create'),

        # must be called with POST to actually succeed. Calling with GET will result in HTTP 400
    url(r'^teacher/groups/(?P<group_id>\d+)/delete/$', 'manage_groups.delete'),

    url(r'^teacher/exams/protocol/(?P<testresult_id>\d+)/$', 'term_supervise.protocol'),
    url(r'^teacher/exams/(?P<exam_id>\d+)/terms/(?P<term_id>\d+)/supervise/$', 'term_supervise.supervise'),
    url(r'^teacher/exams/(?P<exam_id>\d+)/terms/(?P<term_id>\d+)/supervise/ajax/$', 'term_supervise.ajax'),
    url(r'^teacher/exams/(?P<exam_id>\d+)/terms/(?P<term_id>\d+)/setup/ajax/$', 'term_setup.setup_ajax'),
    url(r'^teacher/exams/(?P<exam_id>\d+)/terms/(?P<term_id>\d+)/setup/$', 'term_setup.setup'),
    url(r'^teacher/exams/(?P<exam_id>\d+)/terms/(?P<term_id>\d+)/delete/$', 'manage_exams.delete_term'),
    url(r'^teacher/exams/(?P<exam_id>\d+)/terms/(?P<term_id>\d+)/$', 'manage_exams.term'),
    url(r'^teacher/exams/table/(?P<exam_id>\d+)/$', 'gentable.gentable'),
    url(r'^teacher/exams/$', 'manage_exams.list'),
    url(r'^teacher/exams/create/$', 'manage_exams.create'),
    url(r'^teacher/exams/(?P<exam_id>\d+)/$', 'manage_exams.exam'),
    url(r'^teacher/exams/(?P<exam_id>\d+)/addterm/$', 'manage_exams.addterm'),

        # must be called with POST to actually succeed. Calling with GET will result in HTTP 400
    url(r'^teacher/exams/(?P<exam_id>\d+)/delete/$', 'manage_exams.delete'),

    url(r'^teacher/tests/$', 'tests.list'),
    url(r'^teacher/tests/create/$', 'tests.create'),
    url(r'^teacher/tests/(?P<test_id>\d+)/$', 'tests.test'),
    url(r'^teacher/tests/(?P<test_id>\d+)/delete/$', 'tests.delete_test'),
    url(r'^teacher/tests/(?P<test_id>\d+)/ajax/$', 'tests.test_ajax'),
    url(r'^teacher/tests/(?P<test_id>\d+)/category/create/$', 'tests.create_category'),
    url(r'^teacher/tests/(?P<test_id>\d+)/category/(?P<category_id>\d+)/$', 'tests.category'),
    url(r'^teacher/tests/(?P<test_id>\d+)/category/(?P<category_id>\d+)/delete/$', 'tests.delete_category'),

    url(r'^teacher/tests/(?P<test_id>\d+)/category/(?P<category_id>\d+)/question/new/$', 'tests.create_question'),
    url(r'^teacher/tests/(?P<test_id>\d+)/category/(?P<category_id>\d+)/question/(?P<question_id>\d+)/$', 'tests.question'),
)


urlpatterns += patterns('athena.radmin',

    url(r'^admin/accounts/$', 'manage_accounts.list'),
    url(r'^admin/accounts/(?P<account_id>\d+)/$', 'manage_accounts.account'),

    url(r'^admin/accounts/create/$', 'manage_accounts.create'),

    url(r'^admin/accounts/students/$', 'manage_accounts.view_students'),
    url(r'^admin/accounts/students/(?P<page>\d+)/$', 'manage_accounts.view_students'),

        # must be called with POST to actually succeed. Calling with GET will result in HTTP 400
    url(r'^admin/accounts/(?P<account_id>\d+)/delete/$', 'manage_accounts.delete'),
    url(r'^admin/accounts/(?P<account_id>\d+)/reset_pwd/$', 'manage_accounts.reset_pwd'),
    url(r'^admin/accounts/(?P<account_id>\d+)/su/$', 'manage_accounts.su'),
)
