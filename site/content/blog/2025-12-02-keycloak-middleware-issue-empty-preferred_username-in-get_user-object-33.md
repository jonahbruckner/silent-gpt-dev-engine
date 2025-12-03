+++
title = "Keycloak Middleware Issue: Empty preferred_username in get_user Object"
date = "2025-12-02T10:16:50.567815"
slug = "keycloak-middleware-issue-empty-preferred_username-in-get_user-object"
description = "When integrating Keycloak with your application, you might encounter an issue where the `preferred_username` field in the `get_user` object is empty. This can lead to confusion, especially when you expect this field to be populated with..."
+++

When integrating Keycloak with your application, you might encounter an issue where the `preferred_username` field in the `get_user` object is empty. This can lead to confusion, especially when you expect this field to be populated with the user's username. In this micro-tutorial, we will explore the reasons behind this issue and provide a step-by-step solution to ensure that the `preferred_username` is correctly populated.

## Why this happens

The `preferred_username` field is typically populated from the user’s profile in Keycloak. If this field is empty, it can be due to several reasons:

1. **User Profile Configuration**: The user may not have a `preferred_username` set in their Keycloak profile.
2. **Token Configuration**: The Keycloak client may not be configured to include the `preferred_username` in the access token.
3. **Middleware Implementation**: The middleware responsible for retrieving user information might not be handling the token correctly, leading to missing fields.

## Step-by-step solution

To resolve the issue of the empty `preferred_username`, follow these steps:

### Step 1: Check User Profile in Keycloak

1. Log in to the Keycloak Admin Console.
2. Navigate to **Users** and select the user in question.
3. Check the **Attributes** tab to ensure that the `preferred_username` is set.

### Step 2: Verify Client Configuration

1. In the Keycloak Admin Console, navigate to **Clients**.
2. Select the client that your application uses.
3. Go to the **Mappers** tab and ensure that there is a mapper for `preferred_username`. If it doesn’t exist, create one:
   - Click on **Create**.
   - Set **Name** to `preferred_username`.
   - Set **Mapper Type** to `User Property`.
   - Set **Property** to `username`.
   - Set **Token Claim Name** to `preferred_username`.
   - Enable the **Add to ID token** and **Add to access token** options.

### Step 3: Update Middleware

Ensure your middleware is correctly parsing the token and retrieving the `preferred_username`. Here’s an example of how to implement this in a Python Flask application using the `keycloak` library.

```python
from flask import Flask, request, jsonify
from keycloak import KeycloakOpenID

app = Flask(__name__)

# Initialize Keycloak client
keycloak_openid = KeycloakOpenID(server_url="http://localhost:8080/auth/",
                                  client_id="your-client-id",
                                  realm_name="your-realm")

def get_user():
    token = request.headers.get('Authorization').split(" ")[1]
    user_info = keycloak_openid.userinfo(token)
    
    # Ensure preferred_username is populated
    preferred_username = user_info.get('preferred_username', None)
    if not preferred_username:
        return jsonify({"error": "preferred_username is missing"}), 400
    
    return jsonify({"preferred_username": preferred_username})

@app.route('/user', methods=['GET'])
def user():
    return get_user()

if __name__ == '__main__':
    app.run(debug=True)
```

### Step 4: Test the Configuration

1. After making the above changes, test the application by making a request to the `/user` endpoint.
2. Ensure that the response includes the `preferred_username`.

## Example variation

If you are using a different framework or library, the implementation may vary. Here’s how you might handle the same issue using Django with the `python-keycloak` library.

```python
from django.http import JsonResponse
from keycloak import KeycloakOpenID

keycloak_openid = KeycloakOpenID(server_url="http://localhost:8080/auth/",
                                  client_id="your-client-id",
                                  realm_name="your-realm")

def get_user(request):
    token = request.META.get('HTTP_AUTHORIZATION').split(" ")[1]
    user_info = keycloak_openid.userinfo(token)
    
    preferred_username = user_info.get('preferred_username', None)
    if not preferred_username:
        return JsonResponse({"error": "preferred_username is missing"}, status=400)
    
    return JsonResponse({"preferred_username": preferred_username})

# Add this view to your Django urls.py
```

## Common errors & fixes

1. **Error: `preferred_username` is missing**
   - **Fix**: Ensure that the user has the `preferred_username` set in Keycloak and that the client is configured to map it correctly.

2. **Error: Invalid token**
   - **Fix**: Make sure the token is valid and not expired. Check the token generation process.

3. **Error: Middleware not processing token**
   - **Fix**: Ensure that the middleware is correctly set up in your application and that the authorization header is being sent in requests.

## Cheat sheet summary

- **Check User Profile**: Ensure `preferred_username` is set in the Keycloak user profile.
- **Client Configuration**: Verify that the client has the correct mappers for `preferred_username`.
- **Middleware Implementation**: Ensure your middleware retrieves and processes the token correctly.
- **Testing**: Always test the endpoint to confirm that the `preferred_username` is returned as expected.

By following these steps, you should be able to resolve the issue of the empty `preferred_username` in the `get_user` object when using Keycloak middleware.
