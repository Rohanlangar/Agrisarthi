# TODO: Modify /api/farmers/profile/ to accept farmer_id

## Steps to Complete:
- [x] Update farmers/urls.py: Change the URL pattern for ProfileView from 'profile/' to 'profile/<uuid:farmer_id>/'
- [x] Update farmers/views.py: Modify ProfileView to accept farmer_id parameter in get() and put() methods, fetch farmer by ID instead of using request.user
- [x] For GET: Fetch and return the specified farmer's profile
- [x] For PUT: Allow updating only if the farmer_id matches the authenticated user's ID (to prevent unauthorized updates)
- [x] Test the changes by running the server and making requests to the new endpoint
