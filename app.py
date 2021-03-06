#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash,\
                  redirect, url_for, abort, make_response
from flask_cors import CORS
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import config
from flask_migrate import Migrate
from datetime import datetime
import traceback
from model import setup_db, db, Venue, Show, Artist, VenueGenre, ArtistGenre
from constants import FUTURE, PAST

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
CORS(app)
app.config.from_object('config')
setup_db(app)

# flask migrate
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  # "start_time": "2019-05-21T21:30:00.000Z"
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# Utils.
#----------------------------------------------------------------------------#

def get_venues(venues_raw):
  """
  Groups the venues by city,state as required by the venues page

  Parameters:
    venues_raw (list): list of venue objects to be transformed
  
  Returns:
    venues (list): Appropriately formatted venues, grouped by city and state
  """
  venues = []
  try:
    #get distinct cities 
    distinct_cities = set([(venue.city, venue.state) for venue in venues_raw])
    #prepare data
    for city,state in distinct_cities:
      venue_dict = {'city':city, 'state': state, 'venues':[]}
      venues_in_city = [{'id': venue.id,\
                         'name': venue.name,\
                         'num_upcoming_shows': len(venue.get_shows(FUTURE))}\
                         for venue in venues_raw\
                         if venue.city==city and venue.state==state]
      venue_dict['venues'] = venues_in_city
      venues.append(venue_dict)
  except Exception as e:
    raise e
  return venues

def get_artists(artists_raw):
  """
  Formats the artists as required by the get artists endpoint

  Parameters:
    artists_raw (list): list of artist objects to be transformed
  
  Returns:
    artists (list): Appropriately formatted artists
  """
  artists = []
  try:
    for artist in artists_raw:
      artists.append({
        'id': artist.id,
        'name': artist.name
      })
  except Exception as e:
    raise e
  return artists


def update_genres_venue(new_genres, venue):
  """
  Updates genres for a venue with a new set of genres. Replaces the old genres with new 

  Parameters:
    new_genres (list): List of new genres
    venue (Venue): Venue object that needs a genre update

  """
  try:
    common_genres = []    # common between edit form and existing records  
    
    # step 1: delete 
    for genre in venue.genres:
      if genre.name in new_genres:
        common_genres.append(genre.name)
      else:
        db.session.delete(genre)

    # step 2: add new
    new_uncommon_genres = list(set(new_genres) - set(common_genres))
    for genre in new_uncommon_genres:
      vg = VenueGenre(venue_id=venue.id, name=genre)
      db.session.add(vg)

  except Exception as e:
    raise e

def update_genres_artist(new_genres, artist):
  """
  Updates genres for an artist with a new set of genres. Replaces the old genres with new 

  Parameters:
    new_genres (list): List of new genres
    artist (Artist): Artist object that needs a genre update

  """
  try:
    common_genres = []    # common between edit form and existing records  
    
    # step 1: delete 
    for genre in artist.genres:
      if genre.name in new_genres:
        common_genres.append(genre.name)
      else:
        db.session.delete(genre)

    # step 2: add new
    new_uncommon_genres = list(set(new_genres) - set(common_genres))
    for genre in new_uncommon_genres:
      ag = ArtistGenre(artist_id=artist.id, name=genre)
      db.session.add(ag)

  except Exception as e:
    raise e



#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  """
  Get venues data
  """
  try:
    result = Venue.query.all()
    data = get_venues(result)
    return render_template('pages/venues.html', areas=data);
  except Exception as e:
    print("Error occurred while fetching venues: ",e)
    print(traceback.format_exc())
    abort(500) 
    

@app.route('/venues/search', methods=['POST'])
def search_venues():
  """
  Implement case-insensitive search on artists with partial string search.  
  """
  try:
    search_term = request.form.get('search_term', '')
    results = Venue.query.order_by(Venue.id).filter(Venue.name.ilike('%{}%'.format(search_term))).all()
    match_count = len(results)
    if match_count == 0:
      response = {
        "count": match_count,
        "data": []
      }
    else:
      response = {
        "count": len(results),
        "data": [{"id":venue.id,\
                  "name": venue.name,\
                  "num_upcoming_shows": len(venue.get_shows(FUTURE))}\
                  for venue in results]
      }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))
  except Exception as e:
    print("Error occurred while seraching for venues: ",e)
    print(traceback.format_exc())
    abort(500)
  

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  """
  shows the venue page with the given venue_id
  """
  
  try:
    result = Venue.query.filter_by(id=venue_id).all()
    if len(result) == 0 :
      print("No result for found for venue id {}".format(venue_id))
      abort(404)
    data = result[0].format_all()
  except Exception as e:
    print("Error occured while fetching data for venue ", e)
    print(traceback.format_exc())
    abort(500)
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  """
  Get create venue form
  """
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  """
  Submit new venue form and persist
  """
  try:
    request.get_data()
    genres = request.form.getlist('genres')
    venue_dict = request.form.to_dict()
    seeking_talent = venue_dict['seeking_talent'] == "True"
    venue = Venue(name=venue_dict['name'], city=venue_dict['city'], state=venue_dict['state'],\
                  address=venue_dict['address'], phone=venue_dict['phone'],\
                  facebook_link=venue_dict['facebook_link'],\
                  website_link=venue_dict['website_link'], image_link=venue_dict['image_link'],\
                  seeking_talent=seeking_talent, seeking_description=venue_dict['seeking_description'])
    venue.create(genres)
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
    print("Error while creating new venue: ", e)
    print(traceback.format_exc())
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    abort(500)
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  """
  Deletes venue from DB
  """
  # TODO: Implement Delete Button on UI
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash('Deleted venue '+venue.name+' successfully!')
    return render_template('pages/home.html')
  except Exception as e:
    flash('Error occured while deleting venue ' + venue.name)
    print("Error in deleting venue:: ",e)
    print(traceback.format_exc())
    db.session.rollback()
    abort(500)
  finally:
    db.session.close() 

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  """
  Get artists
  """
  try:
    result = Artist.query.with_entities(Artist.id,Artist.name).all()
    if len(result) == 0:
      print("No results found")
      abort(404)
    data = get_artists(result)
    return render_template('pages/artists.html', artists=data)
  except Exception as e:
    print("Error occured while fetching artists", e)
    print(traceback.format_exc())
    abort(500)
  

@app.route('/artists/search', methods=['POST'])
def search_artists():
  """
  Implements case insesitive search on artists with partial string search
  """
  try:
    search_term = request.form.get('search_term', '')
    results = Artist.query.order_by(Artist.id).filter(Artist.name.ilike('%{}%'.format(search_term))).all()
    match_count = len(results)
    if match_count == 0:
      response = {
        "count": match_count,
        "data": []
      }
    else:
      response = {
        "count": len(results),
        "data": [{"id":artist.id,\
                  "name": artist.name,\
                  "num_upcoming_shows": len(artist.get_shows(FUTURE))}\
                  for artist in results]
      }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))
  except Exception as e:
    print("Error occurred while seraching for artists: ",e)
    print(traceback.format_exc())
    abort(500)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  """shows the venue page with the given venue_id"""
  try:
    result = Artist.query.filter_by(id=artist_id).all()
    if len(result) == 0:
      print("No result for found for artist id {}".format(artist_id))
      abort(404) 
    data = result[0].format_all()
    return render_template('pages/show_artist.html', artist=data)
  except Exception as e:
    print("Error occured while fetching artist", e)
    print(traceback.format_exc())
    abort(500)
  

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  """
  Get data for edit artist page
  """
  form = ArtistForm()
  try:
    result = Artist.query.filter_by(id=artist_id).all()
    if len(result) == 0 :
      print("No result for found for artist id {}".format(artist_id))
      abort(404)
    data = result[0].format_all()
    artist = {
      "id": data["id"],
      "name": data["name"],
      "genres": data["genres"],
      "city": data["city"],
      "state": data["state"],
      "phone": data["phone"],
      "website": data["website"],
      "facebook_link": data["facebook_link"],
      "seeking_venue": data["seeking_venue"],
      "seeking_description": data["seeking_description"],
      "image_link": data["image_link"]
    }
    # TODO: populate form with values from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)
  except Exception as e:
    print("Error occured while fetching data for artist ", e)
    print(traceback.format_exc())
    abort(500)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  """
  Takes values from the form submitted, and updates existing
  artist record with ID <artist_id> using the new attributes
  """
  try:
      # get data from request
      request.get_data()
      new_genres = request.form.getlist('genres')
      artist_dict = request.form.to_dict()

      # get the record to update
      artist = Artist.query.get(artist_id)

      # update
      artist.name = artist_dict["name"]
      artist.city = artist_dict["city"]
      artist.state = artist_dict["state"]
      artist.phone = artist_dict["phone"]
      artist.facebook_link = artist_dict["facebook_link"]
      update_genres_artist(new_genres, artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully edited!')
      return redirect(url_for('show_artist', artist_id=artist_id))
  except Exception as e:
    print("Error in updating records",e)
    db.session.rollback()
    print(traceback.format_exc())
    abort(500)
  finally:
    db.session.close()


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  """
  Get data for edit venue page
  """
  form = VenueForm()
  try:
    result = Venue.query.filter_by(id=venue_id).all()
    if len(result) == 0 :
      print("No result for found for venue id {}".format(venue_id))
      abort(404)
    data = result[0].format_all()
    venue = {
      "id": data["id"],
      "name": data["name"],
      "genres": data["genres"],
      "address": data["address"],
      "city": data["city"],
      "state": data["state"],
      "phone": data["phone"],
      "website": data["website"],
      "facebook_link": data["facebook_link"],
      "seeking_talent": data["seeking_talent"],
      "seeking_description": data["seeking_description"],
      "image_link": data["image_link"]
    }
    return render_template('forms/edit_venue.html', form=form, venue=venue)
  except Exception as e:
    print("Error occured while fetching data for venue ", e)
    print(traceback.format_exc())
    abort(500)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  """
  Takes values from the form submitted, and update existing
  venue record with ID <venue_id> using the new attributes
  """
  try:
      # get data from request
      request.get_data()
      new_genres = request.form.getlist('genres')
      venue_dict = request.form.to_dict()

      # get the record to update
      venue = Venue.query.get(venue_id)

      # update
      venue.name = venue_dict["name"]
      venue.city = venue_dict["city"]
      venue.state = venue_dict["state"]
      venue.address = venue_dict["address"]
      venue.phone = venue_dict["phone"]
      venue.facebook_link = venue_dict["facebook_link"]
      update_genres_venue(new_genres, venue)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully edited!')
      return redirect(url_for('show_venue', venue_id=venue_id))
  except Exception as e:
    print("Error in updating records",e)
    db.session.rollback()
    print(traceback.format_exc())
    abort(500)
  finally:
    db.session.close()

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  """
  Get artist form
  """
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  """
  create artist on form submission
  """
  try:
    request.get_data()
    genres = request.form.getlist('genres')
    artist_dict = request.form.to_dict()
    seeking_venue = artist_dict['seeking_venue'] == "True"
    artist = Artist(name=artist_dict['name'], city=artist_dict['city'], state=artist_dict['state'],\
                  phone=artist_dict['phone'],\
                  facebook_link=artist_dict['facebook_link'],\
                  website_link=artist_dict['website_link'], image_link=artist_dict['image_link'],\
                  seeking_venue=seeking_venue, seeking_description=artist_dict['seeking_description'])
    artist.create(genres)
    flash('artist ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
    print("Error while creating new artist: ", e)
    print(traceback.format_exc())
    flash('An error occurred. artist ' + request.form['name'] + ' could not be listed.')
    abort(500)

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  """Displays list of shows at /shows"""
  shows_raw = Show.query.all()
  data = []
  try:
    for show in shows_raw:
      show_dict = show.get_show_dict()
      if show_dict:
        data.append(show_dict)  
    if len(data) == 0:
      print("No records found for shows")
      abort(404)
  except Exception as e:
    print("Error occured in fetching shows: ",e)
    print(traceback.format_exc())
    abort(500)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  """
  Renders shows create form
  """
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  """
  Called to create new shows in the db, upon submitting new show listing form
  """
  
  try:
    request.get_data()
    show_dict = request.form.to_dict()
    show = Show(venue_id=show_dict["venue_id"], artist_id=show_dict["artist_id"], start_time=show_dict["start_time"])
    show.create()
    flash('Show was successfully listed!')
    return render_template('pages/home.html')  
  except Exception as e:
    print("Error in creating new show: ", e)
    print(traceback.format_exc())
    flash('An error occurred. Show could not be listed.')
    abort(500)
  
  
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

