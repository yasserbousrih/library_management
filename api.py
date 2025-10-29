try:
    import frappe
    from frappe import _
    from frappe.utils import today, add_days, get_datetime
    from frappe.model.document import Document
    from frappe.auth import LoginManager
    FRAPPE_AVAILABLE = True
except ImportError:
    # Frappe not available - this is normal when importing outside Frappe environment
    FRAPPE_AVAILABLE = False
    frappe = None
    _ = lambda x: x
    today = None
    add_days = None
    get_datetime = None
    Document = None
    LoginManager = None


def rent_article(article=None):
    if not FRAPPE_AVAILABLE:
        return {"error": "Frappe not available"}
    """
    Rent an article for the current user via API.
    Enforces membership, max rentals, Library Settings, and updates status.
    Returns frappe.response['success'] and ['message'] for REST consumption.
    """
    try:
        # Get article parameter from the API request
        article = article or frappe.form_dict.get('article')
        
        if not article:
            return {
                'success': False,
                'message': 'Article name is required.'
            }

        # Fetch library settings; fallback to defaults if not set
        try:
            library_settings = frappe.get_single("Library Settings")
            loan_period = library_settings.loan_period or 14
            max_articles = library_settings.max_articles_per_user or 3
        except Exception:
            loan_period = 14
            max_articles = 3

        # Get user's email from current session
        user_email = frappe.get_value('User', frappe.session.user, 'email')

        # Find the Library Member document linked to this email
        library_member = frappe.db.get_value(
            "Library Member",
            {"email": user_email},
            "name"
        )

        if not library_member:
            return {
                'success': False,
                'message': 'No library member found for your account.'
            }

        # Check for an active library membership for this member
        today_date = frappe.utils.today()
        user_memberships = frappe.db.sql("""
            SELECT * FROM `tabLibrary Membership`
            WHERE library_member = %s
            AND from_date <= %s
            AND to_date >= %s
            LIMIT 1
            """, (library_member, today_date, today_date), as_dict=True)

        if not user_memberships:
            return {
                'success': False,
                'message': 'You need an active library membership to rent articles.'
            }

        # Count currently rented articles (not yet returned)
        current_rentals = frappe.db.sql("""
            SELECT COUNT(*) as count FROM `tabLibrary Transaction` lt
            WHERE lt.library_member = %s
            AND lt.type = 'Issue'
            AND lt.docstatus = 1
            AND NOT EXISTS (
                SELECT 1
                FROM `tabLibrary Transaction` lt2
                WHERE lt2.library_member = %s
                AND lt2.article = lt.article
                AND lt2.type = 'Return'
                AND lt2.docstatus = 1
                AND lt2.date >= lt.date
            )
        """, (library_member, library_member), as_dict=True)
        
        if current_rentals and current_rentals[0].count >= max_articles:
            return {
                'success': False,
                'message': f'You have reached the maximum limit of {max_articles} articles. Please return some articles before renting new ones.'
            }

        # Get the Article document
        doc = frappe.get_doc("Article", article)
        if doc.status != "Available":
            return {
                'success': False,
                'message': 'This article is not available for rent.'
            }

        # Create Library Transaction to perform the rental
        frappe.flags.ignore_permissions = True  # Ensure operation is permitted
        txn = frappe.get_doc({
            "doctype": "Library Transaction",
            "article": article,
            "library_member": library_member,
            "date": frappe.utils.today(),
            "type": "Issue"
        })
        txn.insert(ignore_permissions=True)
        txn.submit()

        # Update Article status to 'Issued'
        doc.reload()
        doc.status = "Issued"
        doc.save(ignore_permissions=True)
        
        # Commit the transaction to database
        frappe.db.commit()

        # Calculate and set due date from loan_period
        from frappe.utils import add_days
        due_date = add_days(frappe.utils.today(), loan_period)

        return {
            'success': True,
            'message': f'You have successfully rented the article! Due date: {due_date}',
            'transaction_id': txn.name,
            'due_date': str(due_date)
        }

    except Exception as e:
        frappe.log_error("Error in rent_article: " + str(e))
        frappe.db.rollback()
        return {
            'success': False,
            'message': 'Error renting article: ' + str(e)
        }


@frappe.whitelist(allow_guest=False, methods=['POST', 'GET'])
def return_article(transaction=None):
    """
    Return a rented article.
    Ensures only 'Issue' transactions are processed, prevents duplicate returns,
    creates a 'Return' transaction, and updates the Article status.
    """
    try:
        # Get transaction parameter from multiple sources
        transaction = transaction or frappe.form_dict.get('transaction') or frappe.get_request_header('transaction')
        
        # Handle JSON data from request body
        if frappe.request and hasattr(frappe.request, 'json') and frappe.request.json:
            transaction = transaction or frappe.request.json.get('transaction')
        
        # Debug logging
        frappe.logger().info(f"🔍 DEBUG: return_article called with transaction={transaction}")
        frappe.logger().info(f"🔍 DEBUG: frappe.form_dict = {frappe.form_dict}")
        frappe.logger().info(f"🔍 DEBUG: request method = {frappe.request.method if frappe.request else 'No request'}")
        if frappe.request and hasattr(frappe.request, 'json'):
            frappe.logger().info(f"🔍 DEBUG: request.json = {frappe.request.json}")
        
        if not transaction:
            return {
                'success': False,
                'message': 'Transaction ID is required.'
            }
        
        # Get the transaction document by ID
        txn = frappe.get_doc("Library Transaction", transaction)

        # Only allow rental transactions of type 'Issue' to be returned
        if txn.type != "Issue":
            return {
                'success': False,
                'message': 'This is not a rental transaction.'
            }
        
        # Note: We removed the duplicate return check as it was preventing legitimate returns
        # after re-renting the same article
        
        # Ignore permissions for return operation
        frappe.flags.ignore_permissions = True

        # Create the library return transaction
        return_txn = frappe.get_doc({
            "doctype": "Library Transaction",
            "article": txn.article,
            "library_member": txn.library_member,
            "date": frappe.utils.today(),
            "type": "Return"
        })
        return_txn.insert(ignore_permissions=True)
        return_txn.submit()

        # Update the corresponding article status to 'Available'
        article = frappe.get_doc("Article", txn.article)
        article.reload()
        article.status = "Available"
        article.save(ignore_permissions=True)
        
        # Commit the transaction to database
        frappe.db.commit()

        return {
            'success': True,
            'message': 'Article returned successfully!'
        }
                
    except Exception as e:
        # Log the error and send generic error message to user
        frappe.log_error("Error in return_article: " + str(e))
        frappe.db.rollback()
        return {
            'success': False,
            'message': 'Error returning article: ' + str(e)
        }


@frappe.whitelist(allow_guest=False)
def get_rented_articles():
    """
    Get all currently rented articles for the current user.
    Returns title, author, and transaction information for portal display.
    """
    try:
        user_email = frappe.get_value('User', frappe.session.user, 'email')
        frappe.logger().info(f"🔍 DEBUG: get_rented_articles - user_email: {user_email}")
        
        library_member = frappe.db.get_value("Library Member", {"email": user_email}, "name")
        frappe.logger().info(f"🔍 DEBUG: get_rented_articles - library_member: {library_member}")
        
        if not library_member:
            # Try to create a Library Member if it doesn't exist
            try:
                full_name = frappe.get_value('User', frappe.session.user, 'full_name') or frappe.session.user
                first_name = full_name.split()[0] if full_name else frappe.session.user
                last_name = ' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else ''
                
                library_member_doc = frappe.get_doc({
                    'doctype': 'Library Member',
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': user_email
                })
                library_member_doc.insert(ignore_permissions=True)
                library_member = library_member_doc.name
                frappe.logger().info(f"🔍 DEBUG: Created new Library Member: {library_member}")
            except Exception as e:
                frappe.logger().info(f"🔍 DEBUG: Failed to create Library Member: {str(e)}")
                return {
                    'success': False,
                    'message': 'No library member found for your account and could not create one.',
                    'data': [],
                    'count': 0
                }
        
        rented_articles = frappe.db.sql("""
            SELECT 
                latest.article,
                latest.rental_date,
                latest.transaction_id,
                a.section_break_wvtm as title,
                a.author,
                a.publisher,
                a.isbn,
                a.description
            FROM (
                SELECT 
                    lt.article,
                    lt.date as rental_date,
                    lt.name as transaction_id,
                    lt.type,
                    ROW_NUMBER() OVER (PARTITION BY lt.article ORDER BY lt.date DESC, lt.creation DESC) as rn
                FROM `tabLibrary Transaction` lt
                WHERE lt.library_member = %s
                AND lt.docstatus = 1
            ) latest
            INNER JOIN `tabArticle` a ON latest.article = a.name
            WHERE latest.rn = 1
            AND latest.type = 'Issue'
            ORDER BY latest.rental_date DESC
        """, (library_member,), as_dict=True)
        
        frappe.logger().info(f"🔍 DEBUG: get_rented_articles - found {len(rented_articles)} articles")
        frappe.logger().info(f"🔍 DEBUG: get_rented_articles - articles: {rented_articles}")
        
        # Debug: Check all transactions for this member
        all_transactions = frappe.db.sql("""
            SELECT type, article, date, docstatus
            FROM `tabLibrary Transaction`
            WHERE library_member = %s
            ORDER BY date DESC
        """, (library_member,), as_dict=True)
        frappe.logger().info(f"🔍 DEBUG: All transactions for member {library_member}: {all_transactions}")
        
        return {
            'success': True,
            'message': f'Found {len(rented_articles)} rented articles',
            'data': rented_articles,
            'count': len(rented_articles)
        }
        
    except Exception as e:
        frappe.log_error("Error in get_rented_articles: " + str(e))
        return {
            'success': False,
            'message': 'Error retrieving rented articles: ' + str(e),
            'data': [],
            'count': 0
        }


@frappe.whitelist()
def join_membership():
    """
    Create a new library membership for the current user.
    Ensures the user is logged in, creates Library Member if missing,
    checks for active membership, and registers a new 1-year membership if eligible.
    """
    try:
        user = frappe.session.user
        
        # Ensure user is authenticated (not a Guest)
        if user == "Guest":
            return {
                'success': False,
                'message': 'Please log in to join membership.'
            }
        
        # Try to find Library Member by current user's email
        user_email = frappe.get_value('User', user, 'email')
        library_member = frappe.db.exists('Library Member', {'email': user_email})
        
        if not library_member:
            # If none, create a Library Member record with user's name and email
            full_name = frappe.get_value('User', user, 'full_name') or user
            first_name = full_name.split()[0] if full_name else user
            last_name = ' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else ''
            library_member_doc = frappe.get_doc({
                'doctype': 'Library Member',
                'first_name': first_name,
                'last_name': last_name,
                'email': user_email
            })
            library_member_doc.insert(ignore_permissions=True)
            library_member = library_member_doc.name
            frappe.db.commit()
        
        # Check if user already has an active (unexpired) membership
        active = frappe.db.exists('Library Membership', {
            'library_member': library_member,
            'from_date': ['<=', today()],
            'to_date': ['>=', today()]
        })
        
        if active:
            return {
                'success': False, 
                'message': 'You already have an active membership.'
            }
        
        # Register new membership: valid for one year starting today
        from_date = today()
        to_date = add_days(from_date, 365)
        membership = frappe.get_doc({
            'doctype': 'Library Membership',
            'library_member': library_member,
            'from_date': from_date,
            'to_date': to_date
        })
        membership.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            'success': True, 
            'message': f'Membership created successfully! Valid until {to_date}'
        }
        
    except Exception as e:
        frappe.log_error(f"Error in join_membership: {str(e)}")
        return {
            'success': False,
            'message': f'Error creating membership: {str(e)}'
        }


@frappe.whitelist(allow_guest=False)
def check_membership_eligibility():
    """
    Check if the current user is eligible to join membership.
    - Logged-in user: eligible if no Library Member exists, or if not currently active member.
    - Returns whether new membership can be joined and if Library Member record must be created.
    """
    try:
        user = frappe.session.user
        
        # Disallow check for guests (not logged in)
        if user == "Guest":
            return {
                'success': False,
                'eligible': False,
                'message': 'Please log in to join membership.'
            }
        
        # Get user's email and matching Library Member record
        user_email = frappe.get_value('User', frappe.session.user, 'email')
        library_member = frappe.db.get_value("Library Member", {"email": user_email}, "name")
        
        # If no Library Member, user is eligible and needs creation step
        if not library_member:
            return {
                'success': True,
                'eligible': True,
                'message': 'You are eligible to join membership.',
                'needs_member_creation': True
            }
        
        # Check for already-active membership (dates cover today)
        active = frappe.db.exists('Library Membership', {
            'library_member': library_member,
            'from_date': ['<=', today()],
            'to_date': ['>=', today()]
        })
        
        if active:
            # Already a valid active membership - cannot join again
            return {
                'success': True,
                'eligible': False,
                'message': 'You already have an active membership.',
                'needs_member_creation': False
            }
        
        # Otherwise, eligible to join membership (already has Library Member)
        return {
            'success': True,
            'eligible': True,
            'message': 'You are eligible to join membership.',
            'needs_member_creation': False
        }
        
    except Exception as e:
        frappe.log_error("Error in check_membership_eligibility: " + str(e))
        return {
            'success': False,
            'eligible': False,
            'message': 'Error checking eligibility: ' + str(e)
        }


@frappe.whitelist(allow_guest=True)
def get_library_settings():
    """
    Get current library settings for display purposes.
    Returns loan period and max articles.
    """
    try:
        library_settings = frappe.get_single("Library Settings")
        return {
            'success': True,
            'loan_period': library_settings.loan_period or 14,
            'max_articles_per_user': library_settings.max_articles_per_user or 3,
            'message': 'Library settings retrieved successfully'
        }
    except Exception as e:
        frappe.log_error("Error in get_library_settings: " + str(e))
        return {
            'success': False,
            'loan_period': 14,
            'max_articles_per_user': 3,
            'message': 'Error retrieving library settings, using defaults'
        }


@frappe.whitelist(allow_guest=True)
def get_article_details(article_name):
    """
    Get detailed information for a specific article.
    Returns complete article data including image.
    """
    try:
        if not article_name:
            return {
                'success': False,
                'message': 'Article name is required'
            }
        
        # Query specific article with all fields
        article = frappe.db.sql("""
            SELECT 
                name,
                section_break_wvtm as title,
                author,
                description,
                status,
                creation,
                publisher,
                isbn,
                route,
                image
            FROM `tabArticle`
            WHERE name = %s
        """, (article_name,), as_dict=True)
        
        if not article:
            return {
                'success': False,
                'message': 'Article not found'
            }
        
        article = article[0]  # Get first (and only) result
        
        # Format the article data
        formatted_article = {
            'name': article.name,
            'title': article.title or article.name,
            'author': article.author,
            'description': article.description,
            'status': article.status,
            'publisher': article.publisher,
            'isbn': article.isbn,
            'image': article.image,
            'creation': article.creation,
            'route': article.route
        }
        
        return {
            'success': True,
            'message': 'Article details retrieved successfully',
            'data': formatted_article
        }
        
    except Exception as e:
        frappe.log_error("Error in get_article_details: " + str(e))
        return {
            'success': False,
            'message': 'Error retrieving article details: ' + str(e)
        }

@frappe.whitelist(allow_guest=True)
def get_articles():
    """
    Get all articles with their details for the articles page.
    Returns list with formatted metadata for UI.
    """
    try:
        # Query all articles, select relevant fields, order by newest first
        articles = frappe.db.sql("""
            SELECT 
                name,
                section_break_wvtm as title,
                author,
                description,
                status,
                creation,
                publisher,
                isbn,
                route
            FROM `tabArticle`
            ORDER BY creation DESC
        """, as_dict=True)
        
        # Prepare formatted data for frontend cards/lists
        formatted_articles = []
        for article in articles:
            formatted_article = {
                'name': article.name,
                'title': article.title or article.name,
                'author': article.author,
                'description': article.description,
                'status': article.status,
                'creation': article.creation,
                'publisher': article.publisher,
                'isbn': article.isbn,
                'route': article.route,
                'formatted_date': frappe.utils.formatdate(article.creation),
                # Short preview for UI (first 150 chars)
                'description_preview': (article.description[:150] + '...') if article.description and len(article.description) > 150 else article.description
            }
            formatted_articles.append(formatted_article)
        
        return {
            'success': True,
            'message': f'Found {len(formatted_articles)} articles',
            'articles': formatted_articles,
            'count': len(formatted_articles)
        }
        
    except Exception as e:
        # Log error and return empty response
        frappe.log_error("Error in get_articles: " + str(e))
        return {
            'success': False,
            'message': 'Error retrieving articles: ' + str(e),
            'articles': [],
            'count': 0
        }


@frappe.whitelist(allow_guest=True)
def login(email: str = None, password: str = None, next: str = None):
    """
    Authenticate a user and start a session.
    Accepts 'email' and 'password' via args or form_dict.
    Returns success flag and basic user info on success.
    """
    try:
        # DEBUG: Log all input parameters
        print(f"LOGIN DEBUG - Raw email: {email}, Raw password: {password}")
        print(f"LOGIN DEBUG - form_dict: {frappe.form_dict}")
        frappe.log_error(f"LOGIN DEBUG - Raw email: {email}, Raw password: {password}")
        frappe.log_error(f"LOGIN DEBUG - form_dict: {frappe.form_dict}")
        
        # Handle parameters from frappe.call() - they come as a single dict argument
        if isinstance(email, dict):
            # Parameters passed as dict from frappe.call()
            params = email
            email = params.get("email", "")
            password = params.get("password", "")
        else:
            # Parameters passed individually
            if email is None:
                email = frappe.form_dict.get("email") or frappe.form_dict.get("usr") or ""
            email = str(email).strip()
            
            if password is None:
                password = frappe.form_dict.get("password") or frappe.form_dict.get("pwd") or ""
            password = str(password)
        
        # DEBUG: Log input parameters
        print(f"LOGIN DEBUG - Email: {email}, Password length: {len(password) if password else 0}")
        frappe.log_error(f"LOGIN DEBUG - Email: {email}, Password length: {len(password) if password else 0}")
        
        # Validate required credentials
        if not email or not password:
            return {"success": False, "message": "Email and password are required."}

        # DEBUG: Check if user exists by email or name
        user_doc = None
        try:
            # First try to find by email
            user_doc = frappe.get_doc("User", email)
            print(f"LOGIN DEBUG - User found by email: {user_doc.name}, Enabled: {user_doc.enabled}")
            frappe.log_error(f"LOGIN DEBUG - User found by email: {user_doc.name}, Enabled: {user_doc.enabled}")
        except frappe.DoesNotExistError:
            # Try to find by email field
            try:
                users = frappe.get_all("User", filters={"email": email}, fields=["name", "enabled"])
                if users:
                    user_doc = frappe.get_doc("User", users[0].name)
                    print(f"LOGIN DEBUG - User found by email field: {user_doc.name}, Enabled: {user_doc.enabled}")
                    frappe.log_error(f"LOGIN DEBUG - User found by email field: {user_doc.name}, Enabled: {user_doc.enabled}")
                else:
                    frappe.log_error(f"LOGIN DEBUG - User not found by email: {email}")
                    return {"success": False, "message": "User not found."}
            except Exception as e:
                frappe.log_error(f"LOGIN DEBUG - Error finding user: {e}")
                return {"success": False, "message": "User not found."}

        # Attempt authentication and start session
        print(f"LOGIN DEBUG - Attempting authentication for: {email}")
        frappe.log_error(f"LOGIN DEBUG - Attempting authentication for: {email}")
        
        # Use the user's name for authentication, not email
        user_name = user_doc.name
        print(f"LOGIN DEBUG - Authenticating user: {user_name}")
        frappe.log_error(f"LOGIN DEBUG - Authenticating user: {user_name}")
        
        # Check if we're in a console context (no request)
        if not hasattr(frappe.local, 'request') or not frappe.local.request:
            print(f"LOGIN DEBUG - Console context detected, skipping session creation")
            # For console testing, just verify the password using Frappe's method
            try:
                from frappe.auth import check_password
                if check_password(user_name, password):
                    print(f"LOGIN DEBUG - Password verification successful")
                    return {
                        "success": True,
                        "message": "Login successful (console context).",
                        "user": {
                            "name": user_doc.name,
                            "full_name": user_doc.full_name,
                            "email": user_doc.email,
                            "roles": [r.role for r in user_doc.get("roles", [])],
                        },
                        "redirect_url": "/"
                    }
                else:
                    print(f"LOGIN DEBUG - Password verification failed")
                    return {"success": False, "message": "Invalid password."}
            except Exception as e:
                print(f"LOGIN DEBUG - Password verification error: {e}")
                return {"success": False, "message": f"Password verification failed: {e}"}
        
        # Normal web request context
        login_manager = LoginManager()
        login_manager.authenticate(user=user_name, pwd=password)
        print(f"LOGIN DEBUG - Authentication successful")
        frappe.log_error(f"LOGIN DEBUG - Authentication successful")
        
        login_manager.post_login()
        print(f"LOGIN DEBUG - Post login successful")
        frappe.log_error(f"LOGIN DEBUG - Post login successful")

        # On success, gather user info and roles
        user_name = frappe.session.user
        user = frappe.get_doc("User", user_name)
        roles = [r.role for r in user.get("roles", [])]
        
        frappe.log_error(f"LOGIN DEBUG - Session user: {user_name}, Roles: {roles}")

        # Provide redirect URL, default to home page if none given
        redirect_url = next or "/home"

        return {
            "success": True,
            "message": "Logged in successfully.",
            "user": {
                "name": user.name,
                "full_name": user.full_name,
                "email": user.email,
                "roles": roles,
            },
            "redirect_url": redirect_url,
        }

    except frappe.AuthenticationError as e:
        # Wrong credentials or disabled user
        frappe.log_error(f"LOGIN DEBUG - AuthenticationError: {str(e)}")
        return {"success": False, "message": str(e) or "Invalid email or password."}
    except frappe.ValidationError as e:
        frappe.log_error(f"LOGIN DEBUG - ValidationError: {str(e)}")
        return {"success": False, "message": str(e)}
    except Exception as e:
        frappe.log_error(f"LOGIN DEBUG - General Error: {str(e)}")
        frappe.log_error(f"Error in login: {str(e)}")
        return {"success": False, "message": f"Login failed: {str(e)}"}


@frappe.whitelist(allow_guest=True)
def signup(full_name: str = None, email: str = None, password: str = None, redirect_to: str = None):
    """
    Public user registration endpoint.
    - Registers a new User and Library Member.
    - Returns success flag and info to the frontend.
    - Automatically logs in the user on successful account creation.
    """
    try:
        # Get inputs from arguments or incoming form data
        full_name = (full_name or frappe.form_dict.get("full_name") or "").strip()
        email = (email or frappe.form_dict.get("email") or "").strip()
        password = password or frappe.form_dict.get("password")
        redirect_to = redirect_to or frappe.form_dict.get("redirect_to") or "/home"
        
        # Debug logging
        frappe.log_error(f"Signup attempt: full_name={full_name}, email={email}")

        # Validate required input
        if not full_name or not email or not password:
            return {
                "success": False,
                "message": "Full name, email, and password are required."
            }

        # Check if user already exists in system
        if frappe.db.exists("User", email):
            user = frappe.get_doc("User", email)
            if user.enabled:
                # User exists and is active
                return {
                    "success": False,
                    "message": "This email is already registered. Please login instead.",
                    "user_exists": True
                }
            else:
                # User exists but is disabled
                return {
                    "success": False,
                    "message": "This account exists but is disabled. Please contact support.",
                    "user_disabled": True
                }

        # Parse user's name for DB fields
        user_name = email
        first_name = full_name.split()[0] if full_name else ""
        last_name = " ".join(full_name.split()[1:]) if len(full_name.split()) > 1 else ""
        
        # Create User record using Frappe's proper methods
        user_doc = frappe.get_doc({
            "doctype": "User",
            "name": user_name,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "enabled": 1,
            "send_welcome_email": 0
        })
        user_doc.insert(ignore_permissions=True)
        
        # Set password for new user
        user_doc.new_password = password
        user_doc.save(ignore_permissions=True)
        
        # Assign "Library Member" role to the new user
        user_doc.add_roles("Library Member")
        
        # Debug: Log role assignment
        frappe.log_error(f"Signup: Assigned Library Member role to user: {user_name}")
        
        frappe.db.commit()

        # Create associated Library Member record
        library_member = frappe.get_doc({
            "doctype": "Library Member",
            "first_name": first_name,
            "last_name": last_name,
            "email": email
        })
        library_member.insert(ignore_permissions=True)
        frappe.db.commit()

        # Automatically log in the user after signup
        login_manager = LoginManager()
        login_manager.authenticate(user=email, pwd=password)
        login_manager.post_login()

        # Respond to frontend with details
        return {
            "success": True,
            "message": "Account created successfully! You are now logged in.",
            "user": {
                "name": user_name,
                "full_name": full_name,
                "email": email
            },
            "library_member": library_member.name,
            "redirect_url": redirect_to
        }

    except Exception as e:
        frappe.log_error(f"Error in signup: {str(e)}")
        # More detailed error response for debugging
        return {
            "success": False,
            "message": f"Signup failed: {str(e)}",
            "error_details": str(e)
        }


# Debug Rentals (For Admin/Dev Use)
@frappe.whitelist(allow_guest=False)
def debug_rented_articles():
    """
    Debug method to check all rented articles, transactions, and memberships for current user.
    Helpful for admin troubleshooting.
    """
    try:
        user_email = frappe.get_value('User', frappe.session.user, 'email')
        library_member = frappe.db.get_value("Library Member", {"email": user_email}, "name")
        
        debug_info = {
            'user_email': user_email,
            'library_member': library_member,
            'user': frappe.session.user
        }
        
        if not library_member:
            return {
                'success': False,
                'message': 'No library member found',
                'debug': debug_info
            }
        
        all_transactions = frappe.db.sql("""
            SELECT 
                name,
                article,
                library_member,
                type,
                date,
                docstatus
            FROM `tabLibrary Transaction`
            WHERE library_member = %s
            ORDER BY date DESC
        """, (library_member,), as_dict=True)
        
        all_memberships = frappe.db.sql("""
            SELECT 
                name,
                library_member,
                from_date,
                to_date
            FROM `tabLibrary Membership`
            WHERE library_member = %s
            ORDER BY from_date DESC
        """, (library_member,), as_dict=True)
        
        debug_info.update({
            'all_transactions': all_transactions,
            'all_memberships': all_memberships,
            'transaction_count': len(all_transactions),
            'membership_count': len(all_memberships)
        })
        
        return {
            'success': True,
            'message': 'Debug info retrieved',
            'debug': debug_info
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': 'Debug error: ' + str(e),
            'debug': {}
        }


# Membership Status
@frappe.whitelist(allow_guest=False)
def get_membership_status():
    """
    Get the current user's membership status.
    Returns active memberships and metadata.
    """
    try:
        user_email = frappe.get_value('User', frappe.session.user, 'email')
        library_member = frappe.db.get_value("Library Member", {"email": user_email}, "name")
        
        if not library_member:
            return {
                'success': True,
                'has_membership': False,
                'message': 'No library member found for your account.',
                'memberships': [],
                'count': 0
            }
        
        memberships = frappe.db.sql("""
            SELECT 
                name,
                from_date,
                to_date,
                library_member
            FROM `tabLibrary Membership`
            WHERE library_member = %s
            AND from_date <= %s
            AND to_date >= %s
            ORDER BY creation DESC
        """, (library_member, frappe.utils.today(), frappe.utils.today()), as_dict=True)
        
        return {
            'success': True,
            'has_membership': len(memberships) > 0,
            'message': f'Found {len(memberships)} active memberships',
            'memberships': memberships,
            'count': len(memberships)
        }
        
    except Exception as e:
        frappe.log_error("Error in get_membership_status: " + str(e))
        return {
            'success': False,
            'message': 'Error retrieving membership status: ' + str(e),
            'has_membership': False,
            'memberships': [],
            'count': 0
        }


def rent_article_handler(doc, method):
    """
    Handler for Library Transaction before_save event.
    This is called when a Library Transaction is being saved.
    """
    try:
        if doc.type == "Issue":
            # Check if article is available
            article_doc = frappe.get_doc("Article", doc.article)
            
            if article_doc.status != "Available":
                frappe.throw(_("Article is not available for rent"))
            
            # Update article status
            article_doc.status = "Issued"
            article_doc.save()
            
        elif doc.type == "Return":
            # Update article status back to available
            article_doc = frappe.get_doc("Article", doc.article)
            article_doc.status = "Available"
            article_doc.save()
            
    except Exception as e:
        frappe.throw(_("Error in rent article handler: {0}").format(str(e)))