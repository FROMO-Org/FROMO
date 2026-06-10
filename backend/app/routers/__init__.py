from .events import router as events_router
from .organisations import router as organisations_router
from .profiles import router as profiles_router
from .saved_events import router as saved_events_router
from .bookings import router as bookings_router
from .venues import router as venues_router

all_routers = [events_router, organisations_router, profiles_router, saved_events_router, bookings_router, venues_router]

# Configs and uses all routes in main. Easier to set up. basically is logic in which one of them for the api endpoints calls.
# Stuff like post,get,delete etc.