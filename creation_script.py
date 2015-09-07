__author__ = 'Stefano Tranquillini <stefano.tranquillini@gmail.com>'
from datetime import datetime, timedelta

from api_db_utils import APIDB
from models import User
from gaebasepy.gc_utils import date_to_js_timestamp


user = User.query(User.email == 'stefano.tranquillini@gmail.com').get()
club = APIDB.create_club(name="gymCentral Free Club",
                         description="This club is provided by gymCentral, with a free demo course for everyone who wants to feel the experience of our service.",
                         is_open=True, url="http://gymcentral.net")
# club created
# club = Key('Club',6192449487634432).get()
APIDB.add_owner_to_club(user, club)
# APIDB.add_trainer_to_club(iman, club,status="ACCEPTED")
# Course
data = dict(name="Strength and balance", description="Free course to improve your strength and balance.",
            start_date=date_to_js_timestamp(datetime(2015, 1, 1)),
            end_date=date_to_js_timestamp(datetime(2015, 12, 31)),
            course_type="SCHEDULED", max_level=2)
course = APIDB.create_course(club, **data)
APIDB.add_trainer_to_course(user, course)
# Course created
# course = Key('Course',4785074604081152).get()
# Indicators
data = dict(name="How are you today?", indicator_type="INTEGER", description="How are you today", required=True,
            answer_type='CHECKBOXES',
            possible_answers=[dict(name='1', text='Very bad', value='1'), dict(name='2', text='Not so good', value='2'),
                              dict(name='3', text='Ok', value='3'), dict(name='4', text='Good', value='4'),
                              dict(name='5', text='Very good', value='5')])
how_are_you = APIDB.create_indicator(club, **data)
# how_are_you = Key('Indicator',5275456790069248).get()
data = dict(name="How was the session?", indicator_type="INTEGER", description="How was the session", required=True,
            answer_type='CHECKBOXES',
            possible_answers=[dict(name='e', text='easy', value='-1'), dict(name='m', text='medium', value='0'),
                              dict(name='h', text='hard', value='1')])
how_was_session = APIDB.create_indicator(club, **data)
# how_was_session = Key('Indicator',6401356696911872).get()
data = dict(name="How was the exercise?", indicator_type="INTEGER", description="How was the exercise", required=True,
            answer_type='CHECKBOXES',
            possible_answers=[dict(name='e', text='easy', value='-1'), dict(name='m', text='medium', value='0'),
                              dict(name='h', text='hard', value='1')])
how_was_exercise = APIDB.create_indicator(club, **data)
# print how_was_exercise
# how_was_exercise = Key('Indicator',4993981813358592).get()
data = dict(name="Did you complete the exercise?", indicator_type="BOOLEAN", description="completed", required=True,
            answer_type='CHECKBOXES',
            possible_answers=[dict(name='y', text='yes', value='1'), dict(name='n', text='no', value='0')])
completed = APIDB.create_indicator(club, **data)
# data=dict(name="Do you want to level up?", indicator_type="BOOLEAN", description="level up",required=True,answer_type='CHECKBOXES',possible_answers=[dict(name='y',text='yes',value='1'),dict(name='n',text='no',value='0')])
# level_up = APIDB.create_indicator(club,**data)
# completed = Key('Indicator',5556931766779904).get()

data = dict(
    name="1 Side hip strenghening",
    indicators=[how_was_exercise.id, completed.id],
    levels=[dict(level_number=1,
                 description="Stand up tall beside the bench. Hold on the bench. Keep exercising leg straight and the foot straight forward. Lift the leg out to the side and return. Repeat as in the video.",
                 name='level 1',
                 source=dict(source_type='VIDEO',
                             hd_link='https://player.vimeo.com/external/113606171.hd.mp4?s=5d816b387f9c9995cf78023011c54c5b&profile_id=113',
                             http_live_streaming='https://player.vimeo.com/external/113606171.m3u8?p=high,standard,mobile&s=423466cb08dd0e8ac05a2ab9420a5d1b')
    ),
            dict(level_number=2,
                 description="Strap the weight on your ankle. Stand up tall beside the bench. Hold on the bench. Keep exercising leg straight and the foot straight forward. Lift the leg out to the side and return. Repeat as in the video.",
                 name='level 2',
                 source=dict(source_type='VIDEO',
                             hd_link='https://player.vimeo.com/external/113606172.hd.mp4?s=d9038e766016ace802f6ebd7c885f2e4&profile_id=113',
                             http_live_streaming='https://player.vimeo.com/external/113606172.m3u8?p=high,standard,mobile&s=545bb72cb42b37ca888a71ccb7591fb2')
            )
    ])
first_ex = APIDB.create_activity(club, **data)
# first_ex = Key('Exercise',6682831673622528).get()
data = dict(
    name="2 Back knee strenghting",
    indicators=[how_was_exercise.id, completed.id],
    levels=[
        dict(
            level_number=1,
            description="Stand up tall facing the bench with both hands on the bench. Bend the knee, bringing the foot towards your bottom. Repeat as in the video.",
            name='level 1',
            source=dict(
                source_type='VIDEO',
                hd_link='https://player.vimeo.com/external/113606956.hd.mp4?s=08caa2b8fc294e2b69da65d57db6908a&profile_id=113',
                http_live_streaming='https://player.vimeo.com/external/113606956.m3u8?p=high,standard,mobile&s=ee04a8e522638efef5cea7e7f3c5e52e',
                instruction_link='https://player.vimeo.com/external/106816948.sd.mp4?s=0c14f94af62066f31c42d1d721f54282&profile_id=112'
            )
        ),
        dict(level_number=2,
             description="Strap the weight on your ankle. Stand up tall facing the bench with both hands on the bench. Bend the knee, bringing the foot towards your bottom. Repeat as in the video.",
             name='level 2',
             source=dict(
                 source_type='VIDEO',
                 hd_link='https://player.vimeo.com/external/113606955.hd.mp4?s=8ba0a01ec0e4c5d6111ee6f54a4fd091&profile_id=113',
                 http_live_streaming='https://player.vimeo.com/external/113606955.m3u8?p=high,standard,mobile&s=3cfc0b6a9da7501b43c7c8cc8c031d4b',
                 instruction_link='https://player.vimeo.com/external/106816948.sd.mp4?s=0c14f94af62066f31c42d1d721f54282&profile_id=112'
             )
        )
    ]
)
second_ex = APIDB.create_activity(club, **data)
# second_ex = Key('Exercise',4642138092470272).get()
startdate = datetime(2015, 1, 5)
week = 1
while (startdate < course.end_date):
    enddate = startdate + timedelta(days=7)
    data = dict(name="Session " + str(week), session_type="JOINT",
         start_date=date_to_js_timestamp(startdate),
         end_date=date_to_js_timestamp(enddate),
         activities=[first_ex.id, second_ex.id],
         on_before=[how_are_you.id],
         on_after=[how_was_session.id],)
    week += 1
    startdate += timedelta(days=7)
    print "%s %s" % (week, startdate)
    APIDB.create_session(course, **data)
# session1
# data = dict(name="pre ",session_type="JOINT",
# start_date=date_to_js_timestamp(datetime.now()),
# end_date=date_to_js_timestamp(datetime(2015,9,1,23,59)),
# activities=[first_ex.id,second_ex.id],
# on_before=[how_are_you.id],
# on_after=[how_was_session.id,level_up.id])
# first_session = APIDB.create_session(course,**data)
# # first_session = Key("Session",4916191365693440).get()

# data = dict(name="first day",session_type="JOINT",
# start_date=date_to_js_timestamp(datetime(2015,9,1,00,01)),
# end_date=date_to_js_timestamp(datetime(2015,9,2,23,59)),
# activities=[first_ex.id,second_ex.id],
# on_before=[how_are_you.id],
# on_after=[how_was_session.id,level_up.id])
# second_session = APIDB.create_session(course,**data)

# # second_session = Key("Session",5479141319114752).get()

# #
# data = dict(name="second day",session_type="JOINT",
# start_date=date_to_js_timestamp(datetime(2015,9,2,00,01)),
# end_date=date_to_js_timestamp(datetime(2015,9,3,23,59)),
# 	activities=[first_ex.id,second_ex.id],
# 	on_before=[how_are_you.id],
# 	on_after=[how_was_session.id])
# third_session = APIDB.create_session(course,**data)

# data = dict(name="post",session_type="JOINT",
# 	start_date=date_to_js_timestamp(datetime(2015,9,3,00,01)),
# 	end_date=date_to_js_timestamp(datetime(2015,12,31,23,59)),
# 	activities=[first_ex.id,second_ex.id],
# 	on_before=[how_are_you.id],
# 	on_after=[how_was_session.id])
# fourth_session = APIDB.create_session(course,**data)# third_session = Key("Session",6605041225957376).get()

# gc1 = User.query(User.email=='gymcentralnet.trainee.1@gmail.com').get()
# gc2 = User.query(User.email=='gymcentralnet.trainee.2@gmail.com').get()
# gc3 = User.query(User.email=='gymcentralnet.trainee.3@gmail.com').get()

# APIDB.add_member_to_course(gc1,course,status="ACCEPTED")
# APIDB.add_member_to_course(gc2,course,status="ACCEPTED",level=2)
# APIDB.add_member_to_course(gc3,course,status="ACCEPTED")
# iman = User.query(User.email=='iman.khaghani@gmail.com').get()

# APIDB.add_member_to_course(iman,course,status="ACCEPTED")
