from django.template import RequestContext
from django.shortcuts import render_to_response
from login.forms import RegistrationForm
from login.forms import LoginForm
from webstore.models import StoreItem, StoreCategory, Order, OrderItemCorrect
from login.models import UserProfile
from django.http import HttpResponse
from webstore.bing_search import run_query
import simplejson as json
from haystack.query import SearchQuerySet
from django.forms.models import model_to_dict
from copy import deepcopy
from django.core import serializers
from django.utils import timezone

#### need to initialize the cart here so it is accesible initially
def webstore(request,id):
	context = RequestContext(request)    
	#if request.method == 'GET':
	ids = StoreCategory.objects.get(categoryName=id)
	items = StoreItem.objects.filter(category_id=ids.id).all()
	item_categories = StoreCategory.objects.all();
	return render_to_response('store/shop-homepage.html', {'items': items, 'item_categories': item_categories, 'regform': RegistrationForm(),'loginform': LoginForm()},context)

def featured(request):
	
	context = RequestContext(request)
	items = StoreItem.objects.all()
	return render_to_response('index.html',{'success': True, 'items': items}, context)

def getImage(request, id, directory, image_name):
	imagelocation = directory + "/" + image_name
	print imagelocation
	image_data = open(imagelocation, "rb").read()
	return HttpResponse(image_data, mimetype="image/png")
	
def home(request):
	context = RequestContext(request)
	return render_to_response('store/shop-homepage.html', {'regform': RegistrationForm(),'loginform': LoginForm()},context )

def searchStore(request):
	context = RequestContext(request)
	
	sqs = SearchQuerySet().filter(content=request.POST.get('search_text'))
	result_list = serializers.serialize('json', StoreItem.objects.filter(itemName__icontains= request.POST.get('search_text') ), fields=('category','itemName','itemNameid','description','price','picture'))
	
	return HttpResponse(result_list, content_type='application/json')

def autocomplete(request):
	sqs = SearchQuerySet().autocomplete(content_auto=request.GET.get('q', ''))[:5]
	suggestions = [result.itemName for result in sqs]
	# Make sure you return a JSON object, not a bare list.
	# Otherwise, you could be vulnerable to an XSS attack.
	the_data = json.dumps({
		'results': suggestions
	})
	
	return HttpResponse(the_data, content_type='application/json')


def query(request):
	context = RequestContext(request)
	return render_to_response('store/shop-homepage.html',{'success': True},context)

# The car is stored in the session as a dictionary of a dictionary that has
# the primary key of an item and how many were added
def buttonTest(request):
	print "pressed button"
	context = RequestContext(request)
	return render_to_response('store/shop-homepage.html',{'success': True}, context)

def addToCart(request, itemKey, quantity):
	#print "FLUSHING THE SESSION"
	#request.session.flush()

	print itemKey
	context = RequestContext(request)
	print request.session.keys()

	if quantity <= 0:
		removeFromCart(request, itemKey)
	if not 'cartList' in request.session:
		#request.session['cartList'] = {itemKey : {"quantity" : quantity}}
		print "making a new cart"
		print [itemKey, quantity]
		request.session['cartList'] = []
		request.session['cartList'].append([itemKey, quantity])
		# make a new cart
	else:
		print "inserting to cart"
		print [itemKey, quantity]
		alreadydone = False
		for index in xrange(len(request.session['cartList'])):
			print "at index ", index 
			print "looking at ", request.session['cartList'][index]
			if itemKey == request.session['cartList'][index][0]: # already in list
				print "already in cart, updating quantity"
				request.session['cartList'][index][1] = quantity
				alreadydone = True
				break
		if not alreadydone: # append the new item to the cart
			print "appending to cart"
			request.session['cartList'].append([itemKey, quantity])
		# this works for modifying quantity as well as adding
	print "printing session cart before save"
	print request.session['cartList']
	request.session.save()
	cart = deepcopy(request.session['cartList']) # wondering if this is needed...
	print "printing cart list"
	print cart

	sendlist = json.dumps({'cart':cart})
	return HttpResponse(sendlist, content_type='application/json')
	#return render_to_response('store/shop-homepage.html',{'cart':cart,'success': True},context)

def removeFromCart(request, itemKey):
	context = RequestContext(request)
	if 'cartList' in request.session and itemKey in request.session['cartList']:
		pass
		#request.session['cartList'].pop(itemKey)
	request.session.save()
	return render_to_response('store/shop-homepage.html',{'success': True},context)

def deleteCart(request):
	context = RequestContext(request)
	if 'cartList' in request.session:
		request.session.pop('cartList')
	request.session.save()
	return render_to_response('store/shop-homepage.html',{'success': True},context)

# How this works:
# loop through the item names that are in the cart.
# Fetch the matching storeitem
# link that into an orderitem (an order item has a seperate price field and quantity field)
	# that price will just be the same for now. In the future, that might allow
	# for bookstore pricing or promotions to be figured in here.
	# quantity is just how many of the item are being ordered
# link each of those orderitems into a new order object
# save and return that order object to use it for filling in the template
def checkout(request):

	context = RequestContext(request)
	cart = request.session['cartList']
	myOrder = Order() # we have an order object now
	myOrder.orderDate = timezone.now() # date for the order is now
	# these will need to come after probably - I just want to save it
	myOrder.shippingCost = 1
	myOrder.totalCost = 2
	myOrder.save()


	for itemlist in cart: # remember that cart is an array of arrays that have name, quantity, price
		#orderItem = OrderItemCorrect()
		#print "cleaning the order item model"
		# orderItem.full_clean()
		storeItem = StoreItem.objects.get(itemNameid=itemlist[0])
		orderItem = OrderItemCorrect(
			order = myOrder,
			itemID = storeItem,
			itemCost = storeItem.price,
			itemQuantity = int(itemlist[1])
		)
		orderItem.save(force_insert=True)
	
	itemsInOrder = myOrder.orderitemcorrect_set.all()
	
	subtotal = 0
	for items in itemsInOrder:
		subtotal += items.itemCost
	#calculate shipping cost, temporary placeholder
	myOrder.totalCost = subtotal + myOrder.shippingCost
	myOrder.save()
	cents = myOrder.totalCost * 100


	return render_to_response('store/checkout.html',{'cents':cents,'order':myOrder, 'items':itemsInOrder, 'success': True},context)

def payment(request):
	context = RequestContext(request)
	import stripe
	# Set your secret key: remember to change this to your live secret key in production
	# See your keys here https://manage.stripe.com/account
	stripe.api_key = "sk_test_5LSNQ19L2N0gk7euXWWfWsPO"

	# Get the credit card details submitted by the form
	token = request.POST['stripeToken']
	# Slightly ugly, but functional way of getting value from stripe checkout gui
	cents = int(float(request.POST['amount_in_cents']))
	try:
		charge = stripe.Charge.create(
      	amount=cents, # amount in cents, again
      	currency="usd",
      	card=token,
      	description="payinguser@example.com" #need to deal with this
  		)
		pass
	except stripe.error.CardError, e:
		# Since it's a decline, stripe.error.CardError will be caught
		body = e.json_body
		err  = body['error']

		print "Status is: %s" % e.http_status
		print "Type is: %s" % err['type']
		print "Code is: %s" % err['code']
		# param is '' in this case
		print "Param is: %s" % err['param']
		print "Message is: %s" % err['message']
	except stripe.error.InvalidRequestError, e:
		# Invalid parameters were supplied to Stripe's API
		pass
	except stripe.error.AuthenticationError, e:
		# Authentication with Stripe's API failed
		# (maybe you changed API keys recently)
		pass
	except stripe.error.APIConnectionError, e:
		# Network communication with Stripe failed
		pass
	except stripe.error.StripeError, e:
		# Display a very generic error to the user, and maybe send
		# yourself an email
		pass
	except Exception, e:
		# Something else happened, completely unrelated to Stripe
		pass

	return render_to_response('store/checkout.html',{'success' : True},context)