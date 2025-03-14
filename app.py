import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

from api.user_handler import authenticate_user, create_user
from api.categories_handler import get_all_categories, get_category_by_id, add_category, update_category, get_categories_with_auction_count,delete_category_by_id
from api.auctions_handler import get_all_auctions, get_auction_by_id, insert_auction, update_auction_in_db, cancel_auction_in_db, get_top_auctions, is_auction_active
from api.messages_handler import create_message, get_all_messages, mark_message_as_responded
from api.bids_handler import place_bid, get_highest_bid, get_all_bids_for_auction, delete_bid, get_highest_bid_for_auction
from api.likedislike_handler import add_like_dislike, get_likes_dislikes
from api.auto_bidding_handler import add_or_update_auto_bid
from werkzeug.exceptions import Forbidden

# Load the configuration
with open('config.json') as config_file:
    config = json.load(config_file)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = config['app']['secret_key']
app.config['DEBUG'] = config['app']['debug']

# Get the database path
DB_PATH = config['database']['path']

#region Regular routes

@app.route('/')
def home():
    top_auctions = get_top_auctions()  # Fetch top 3 auctions
    return render_template(
        'index.html',
        logged_in=session.get('logged_in', False),
        isAdmin=session.get('is_admin', False),
        top_auctions=top_auctions
    )

@app.route('/signup', endpoint='signup')
def signup_page():
    """Render the signup page."""
    return render_template('signup.html')

@app.route('/login', endpoint='login')
def login_page():
    """Render the login page."""
    return render_template(
        'login.html',
        logged_in=session.get('logged_in', False),
        username=session.get('username', None),
        isAdmin=session.get('is_admin', False)
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/auctions')
def auctions():
     return render_template(
        'auctions.html',
        logged_in=session.get('logged_in', False),
        isAdmin=session.get('is_admin', False)
    )

@app.route('/contact')
def contact():
    return render_template(
        'contact.html',
        logged_in=session.get('logged_in', False),
        isAdmin=session.get('is_admin', False)
    )

@app.route('/admin/backoffice')
def backoffice():
    # Check if the user is logged in and has admin privileges
    if not session.get('logged_in') or not session.get('is_admin'):
        raise Forbidden()
    return render_template(
        'backoffice.html',
        logged_in=session.get('logged_in', False),
        isAdmin=session.get('is_admin', False)
    )

#endregion

#region ErrorHandling
@app.errorhandler(403)
def forbidden_error(e):
    return render_template(
        'unauthorized.html',
        logged_in=session.get('logged_in', False),
        isAdmin=session.get('is_admin', False)
    ), 403

#endregion

#region API Endpoints

#region login/logout
@app.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint for user login."""
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Authenticate user using the database
    user = authenticate_user(email, password)

    if user:
        # Store session data
        session['logged_in'] = True
        session['username'] = user['username']
        session['is_admin'] = bool(user['is_admin'])
        session['user_id'] = user['id']

        return jsonify({
            "success": True,
            "message": "Login successful",
            "username": user['username'],
            "is_admin": user['is_admin']
        })
    else:
        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401
    
@app.route('/api/logout', methods=['POST'])
def api_logout():
    """API endpoint for logging out."""
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"})
#endregion

#region Auctions

@app.route('/api/auctions', methods=['POST'])
def create_auction():
    data = request.json
    title = data.get("title")
    description = data.get("description")
    starting_bid = data.get("starting_bid")
    category_id = data.get("category_id")
    start_datetime = data.get("start_datetime")
    end_datetime = data.get("end_datetime")
    created_by = session.get("user_id")

    if not all([title, description, starting_bid, category_id, start_datetime, end_datetime, created_by]):
        return jsonify({"success": False, "message": "All fields are required."}), 400

    try:
        insert_auction(title, description, starting_bid, category_id, start_datetime, end_datetime, created_by)
        return jsonify({"success": True, "message": "Auction created successfully!"}), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/auctions/<int:auction_id>', methods=['PUT'])
def update_auction(auction_id):
    """API endpoint to update an existing auction."""
    if not session.get("logged_in"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.json
    title = data.get("title")
    description = data.get("description")
    starting_bid = data.get("starting_bid")
    category_id = data.get("category_id")
    start_datetime = data.get("start_datetime")  # Include start_datetime
    end_datetime = data.get("end_datetime")

    # Validate required fields
    if not all([title, description, starting_bid, category_id, start_datetime, end_datetime]):
        return jsonify({"success": False, "message": "All fields are required."}), 400

    try:
        # Call the function with all required parameters
        update_auction_in_db(
            auction_id,
            title,
            description,
            starting_bid,
            category_id,
            start_datetime,
            end_datetime
        )
        return jsonify({"success": True, "message": "Auction updated successfully!"}), 200
    except Exception as e:
        app.logger.error(f"Error updating auction {auction_id}: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@app.route('/api/auctions/<int:auction_id>/<action>', methods=['POST'])
def update_likes(auction_id, action):
    try:
        auction = get_auction_by_id(auction_id)
        if not auction:
            return jsonify({"success": False, "message": "Auction not found"}), 404

        if action == 'like':
            auction["likes"] += 1
        elif action == 'dislike':
            auction["dislikes"] += 1
        else:
            return jsonify({"success": False, "message": "Invalid action"}), 400

        # Persist changes
        update_auction_in_db(
            auction_id,
            auction["title"],
            auction["description"],
            auction["starting_bid"],
            auction["category_id"],
            auction["end_datetime"],
        )

        return jsonify({"success": True, "likes": auction["likes"], "dislikes": auction["dislikes"]}), 200
    except Exception as e:
        app.logger.error(f"Error in update_likes: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@app.route('/api/auctions/<int:auction_id>', methods=['DELETE'])
def cancel_auction(auction_id):
    """API endpoint to cancel an auction."""
    try:
        cancel_auction_in_db(auction_id)
        return jsonify({"success": True, "message": "Auction canceled successfully!"}), 200
    except Exception as e:
        app.logger.error(f"Error canceling auction {auction_id}: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@app.route('/api/auctions/<int:auction_id>/bid', methods=['POST'])
def api_place_bid(auction_id):
    """
    API endpoint to place a bid on an auction.
    """
    if not session.get('logged_in'):
        return jsonify({"success": False, "message": "You must be logged in to place a bid."}), 401

    data = request.json
    bid_amount = data.get('amount')

    if bid_amount is None or bid_amount <= 0:
        return jsonify({"success": False, "message": "Invalid bid amount."}), 400

    try:
        # Check if the auction is active
        if not is_auction_active(auction_id):
            return jsonify({"success": False, "message": "Auction has ended or is canceled."}), 400

        # Get the highest bid or starting bid
        highest_bid = get_highest_bid(auction_id)
        auction = get_auction_by_id(auction_id)
        starting_bid = auction['starting_bid']

        # Ensure the bid is higher than the current highest bid or starting bid
        minimum_bid = max(highest_bid if highest_bid else starting_bid, starting_bid)
        if bid_amount <= minimum_bid:
            return jsonify({"success": False, "message": f"Bid must be higher than ${minimum_bid}."}), 400

        # Place the bid
        user_id = session.get('user_id')
        place_bid(auction_id, user_id, bid_amount)
        return jsonify({"success": True, "message": "Bid placed successfully!"}), 201
    except Exception as e:
        app.logger.error(f"Error placing bid: {e}")
        return jsonify({"success": False, "message": "Internal server error."}), 500

@app.route('/api/auctions/<int:auction_id>/bids', methods=['GET'])
def api_get_bids(auction_id):
    """API endpoint to fetch all bids for an auction."""
    try:
        bids = get_all_bids_for_auction(auction_id)
        return jsonify({"success": True, "bids": bids}), 200
    except Exception as e:
        app.logger.error(f"Error fetching bids for auction {auction_id}: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500
    
@app.route('/api/auctions/all', methods=['GET'])
def api_get_all_auctions():
    """
    API endpoint to fetch all auctions.
    Front end gets only non-canceled auctions; back office gets all.
    Optional query parameter 'limit' to restrict the number of results.
    """
    try:
        # Get the 'limit' query parameter, default to None
        limit = request.args.get('limit', default=None, type=int)

        # Determine if canceled auctions should be included
        include_canceled = request.args.get('include_canceled', 'false').lower() == 'true'

        # Fetch auctions
        auctions = get_all_auctions(limit=limit, include_canceled=include_canceled)

        # Convert rows to dictionaries for JSON serialization and include likes/dislikes
        auctions_list = []
        for auction in auctions:
            auction_dict = dict(auction)
            # Fetch likes/dislikes for the auction
            likes_dislikes = get_likes_dislikes(auction_dict['id'])
            auction_dict['likes'] = likes_dislikes['likes']
            auction_dict['dislikes'] = likes_dislikes['dislikes']
            
            # Fetch the highest bid for the auction
            highest_bid_info = get_highest_bid_for_auction(auction_dict['id'])
            if highest_bid_info:
                auction_dict["highest_bid"] = highest_bid_info["highest_bid"]
                auction_dict["highest_bidder_email"] = highest_bid_info["email"]
            else:
                auction_dict["highest_bid"] = None
                auction_dict["highest_bidder_email"] = None
            
            auctions_list.append(auction_dict)

        return jsonify({
            "success": True,
            "auctions": auctions_list
        }), 200
    except Exception as e:
        app.logger.error(f"Error fetching auctions: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@app.route('/api/auctions/<int:auction_id>/autobid', methods=['POST'])
def set_auto_bid(auction_id):
    data = request.json
    max_bid = data.get("max_bid")
    increment = data.get("increment", 1)
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        add_or_update_auto_bid(auction_id, user_id, max_bid, increment)
        return jsonify({"success": True, "message": "Auto-bid set successfully!"}), 201
    except Exception as e:
        app.logger.error(f"Error setting auto-bid for auction {auction_id}: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500
    
@app.route('/api/auctions/<int:id>', methods=['GET'])
def api_get_auction_by_id(id):
    """
    API endpoint to fetch a single auction by its ID.
    Example: /api/auctions/3
    """
    try:
        # Fetch auction by ID
        auction = get_auction_by_id(id)

        if auction:
            return jsonify({
                "success": True,
                "auction": dict(auction)
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Auction not found"
            }), 404
    except Exception as e:
        app.logger.error(f"Error fetching auction by ID {id}: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

#endregion

#region Bids
@app.route('/api/bids/<int:bid_id>', methods=['DELETE'])
def delete_bid_api(bid_id):
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    try:
        success = delete_bid(bid_id)
        if success:
            return jsonify({'success': True, 'message': 'Bid deleted successfully.'})
        else:
            return jsonify({'success': False, 'message': 'Failed to delete bid.'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


#endregion

#region Categories
@app.route('/api/categories', methods=['GET'])
def api_get_categories():
    """Fetch all categories."""
    try:
        categories = get_all_categories()
        return jsonify({"success": True, "categories": [dict(category) for category in categories]}), 200
    except Exception as e:
        app.logger.error(f"Error fetching categories: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@app.route('/api/categories/<int:category_id>', methods=['GET'])
def api_get_category_by_id(category_id):
    """Fetch a single category by its ID."""
    try:
        category = get_category_by_id(category_id)
        if category:
            return jsonify({"success": True, "category": dict(category)}), 200
        else:
            return jsonify({"success": False, "message": "Category not found"}), 404
    except Exception as e:
        app.logger.error(f"Error fetching category {category_id}: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500
    
@app.route('/api/categories/edit', methods=['POST'])
def api_edit_category():
    data = request.json
    category_id = data.get('category_id')
    name = data.get('name')
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        update_category(category_id, name, user_id)
        return jsonify({"success": True, "message": "Category updated successfully"}), 200
    except Exception as e:
        app.logger.error(f"Error editing category: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """
    API endpoint to delete a category.
    Ensures the category has no associated auctions before deletion.
    """
    try:
        success, message = delete_category_by_id(category_id)

        if not success:
            return jsonify({"success": False, "message": message}), 400

        return jsonify({"success": True, "message": message}), 200

    except Exception as e:
        app.logger.error(f"Error deleting category {category_id}: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@app.route('/api/categories/with-auction-count', methods=['GET'])
def api_get_categories_with_auction_count():
    """Fetch all categories with the count of auctions under each."""
    try:
        categories = get_categories_with_auction_count()
        return jsonify({
            "success": True,
            "categories": [dict(category) for category in categories]
        }), 200
    except Exception as e:
        app.logger.error(f"Error fetching categories with auction count: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@app.route('/api/categories/add', methods=['POST'])
def api_add_category():
    data = request.json
    name = data.get('name')
    user_id = session.get('user_id')

    if not user_id:
        app.logger.error("User ID missing from session.")
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        add_category(name, user_id)
        return jsonify({"success": True, "message": "Category added successfully"}), 200
    except Exception as e:
        app.logger.error(f"Error adding category: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500
  
#endregion

#region Likes/dislikes
@app.route('/api/auctions/<int:auction_id>/like', methods=['POST'])
def like_auction(auction_id):
    if not session.get('logged_in'):
        return jsonify({"success": False, "message": "You must be logged in to like auctions."}), 401

    user_id = session.get('user_id')
    try:
        add_like_dislike(user_id, auction_id, 1)
        counts = get_likes_dislikes(auction_id)
        return jsonify({"success": True, "likes": counts['likes'], "dislikes": counts['dislikes']})
    except Exception as e:
        app.logger.error(f"Error liking auction {auction_id}: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@app.route('/api/auctions/<int:auction_id>/dislike', methods=['POST'])
def dislike_auction(auction_id):
    if not session.get('logged_in'):
        return jsonify({"success": False, "message": "You must be logged in to dislike auctions."}), 401

    user_id = session.get('user_id')
    try:
        add_like_dislike(user_id, auction_id, -1)
        counts = get_likes_dislikes(auction_id)
        return jsonify({"success": True, "likes": counts['likes'], "dislikes": counts['dislikes']})
    except Exception as e:
        app.logger.error(f"Error disliking auction {auction_id}: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500
#endregion

#region Messages
@app.route('/api/messages', methods=['POST'])
def api_create_message():
    """API endpoint to handle contact form submissions."""
    data = request.json

    # Extract form data
    sender_name = data.get('name')
    sender_email = data.get('email')
    message = data.get('message')

    # Validate data
    if not sender_name or not sender_email or not message:
        return jsonify({"success": False, "message": "All fields are required."}), 400

    try:
        # Save the message to the Messages table
        create_message(sender_name, sender_email, message)
        return jsonify({"success": True, "message": "Message sent successfully!"}), 200
    except Exception as e:
        app.logger.error(f"Error saving message: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@app.route('/api/messages', methods=['GET'])
def api_get_all_messages():
    try:
        messages = get_all_messages()
        return jsonify({
            "success": True,
            "messages": [dict(message) for message in messages]
        }), 200
    except Exception as e:
        app.logger.error(f"Error fetching messages: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@app.route('/api/messages/respond/<int:message_id>', methods=['POST'])
def api_mark_message_as_responded(message_id):
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        mark_message_as_responded(message_id, user_id)
        return jsonify({"success": True, "message": "Message marked as responded"}), 200
    except Exception as e:
        app.logger.error(f"Error marking message as responded: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

#endregion

#region Signup
@app.route('/api/signup', methods=['POST'], endpoint='api_signup')
def api_signup():
    """
    API endpoint to handle user signup.
    """
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # Validate required fields
    if not all([username, email, password]):
        return jsonify({"success": False, "message": "All fields are required."}), 400

    # Call create_user and handle its result
    success, message = create_user(username=username, email=email, password_hash=password, is_admin=False)

    if success:
        return jsonify({"success": True, "message": message}), 201
    else:
        return jsonify({"success": False, "message": message}), 400



#endregion
#endregion



# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
