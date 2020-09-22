#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import config
from flask_migrate import Migrate
from sqlalchemy.sql.functions import func
from datetime import datetime
import traceback
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

# TODO: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS

db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(200))
    shows = db.relationship("Show", backref=db.backref('venues', lazy=True))
    genres = db.relationship("VenueGenre", backref=db.backref('venues', lazy=True))

    def __init__(self, name, city, state, address, phone, facebook_link,\
                 website_link, image_link, seeking_talent, seeking_description):
      self.name = name
      self.city = city
      self.state = state
      self.address = address
      self.phone = phone
      self.facebook_link = facebook_link
      self.website_link = website_link
      self.image_link = image_link
      self.seeking_talent = seeking_talent
      self.seeking_description = seeking_description
      
    def get_past_shows(self):
      shows = []
      try:
        shows_raw = list(filter(lambda x: x.start_time < datetime.now(), self.shows))
        for show in shows_raw:
          shows.append({'artist_id': show.artists.id,\
                        'artist_name': show.artists.name,\
                        'artist_image_link': show.artists.image_link,\
                        'start_time': show.start_time.isoformat()})
      except Exception as e:
        raise e
      return shows
      
    def get_future_shows(self):
      shows = []
      try:
        shows_raw = list(filter(lambda x: x.start_time > datetime.now(), self.shows))
        for show in shows_raw:
          shows.append({'artist_id': show.artists.id,\
                        'artist_name': show.artists.name,\
                        'artist_image_link': show.artists.image_link,\
                        'start_time': show.start_time.isoformat()})  
      except Exception as e:
        raise e      
      return shows
      
    
    def get_genres(self):
      genres = []
      try:
        genres = [genre.name for genre in self.genres]
      except Exception as e:
        raise e
      return genres

    
    def format_all(self):
      venue_dict = {}
      try:
        upcoming_shows = self.get_future_shows()
        past_shows = self.get_past_shows()
        genres = self.get_genres()
        venue_dict = {
          'id': self.id, 
          'name': self.name, 
          'genres': genres, 
          'address': self.address, 
          'city': self.city, 
          'state': self.state, 
          'phone': self.phone, 
          'website': self.website_link, 
          'facebook_link': self.facebook_link, 
          'seeking_talent': self.seeking_talent, 
          'seeking_description': self.seeking_description, 
          'image_link': self.image_link, 
          'past_shows': past_shows, 
          'upcoming_shows': upcoming_shows,
          'past_shows_count': len(past_shows), 
          'upcoming_shows_count': len(upcoming_shows)
        }
      except Exception as e:
        raise e
      return venue_dict

    def create(self, genres):
      is_created = False
      try:
        for genre in genres:
          vg = VenueGenre(name=genre)
          self.genres.append(vg)
        db.session.add(self)
        db.session.commit()
        is_created = True
      except Exception as e:
        db.session.rollback()
        raise e
      finally:
        db.session.close()
      return is_created
    
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Show(db.Model): 
    """
    Follows association object pattern
    """
    __tablename__ = 'show'

    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id', ondelete='CASCADE'), primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id', ondelete='CASCADE'), primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    artists = db.relationship('Artist', backref=db.backref('shows', lazy=True))


class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(200))
    genres = db.relationship("ArtistGenre", backref=db.backref('artists', lazy=True))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

    def __init__(self):
      pass

    def get_future_shows(self):
      future_shows = []
      try:
        shows_raw = list(filter(lambda show: show.start_time > datetime.now(), self.shows))
        for show in shows_raw:
          venues = self.show.venue
          future_shows.append({'venue_id': show.venues.id,\
                          'venue_name': show.venues.name,\
                          'venue_image_link': show.venues.image_link,\
                          'start_time': show.start_time.isoformat()})
      except Exception as e:
        raise e
      return future_shows
      
    def get_past_shows(self):
      future_shows = []
      try:
        shows_raw = list(filter(lambda show: show.start_time < datetime.now(), self.shows))
        for show in shows_raw:
          venues = self.show.venue
          future_shows.append({'venue_id': show.venues.id,\
                          'venue_name': show.venues.name,\
                          'venue_image_link': show.venues.image_link,\
                          'start_time': show.start_time.isoformat()})
      except Exception as e:
        raise e
      return future_shows  
  
    def get_genres(self):
      genres = []
      try:
        genres = [genre.name for genre in self.genres]
      except Exception as e:
        raise e
      return genres 

    def format_all(self):
      artist_dict = {}
      try:
        upcoming_shows = self.get_future_shows()
        past_shows = self.get_past_shows()
        genres = self.get_genres()
        artist_dict = {
          'id': self.id, 
          'name': self.name, 
          'genres': genres,  
          'city': self.city, 
          'state': self.state, 
          'phone': self.phone, 
          'website': self.website_link, 
          'facebook_link': self.facebook_link, 
          'seeking_venue': self.seeking_venue, 
          'seeking_description': self.seeking_description, 
          'image_link': self.image_link, 
          'past_shows': past_shows, 
          'upcoming_shows': upcoming_shows,
          'past_shows_count': len(past_shows), 
          'upcoming_shows_count': len(upcoming_shows)
        }
      except Exception as e:
        raise e
      return artist_dict



class VenueGenre(db.Model):
    __tablename__ = 'venuegenre'
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id', ondelete='CASCADE'), primary_key=True)
    name = db.Column(db.String(30), nullable=False, primary_key=True)

class ArtistGenre(db.Model):
    __tablename__ = 'artistgenre'
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id', ondelete='CASCADE'), primary_key=True)
    name = db.Column(db.String(30), nullable=False, primary_key=True)

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

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


def get_venues(venues_raw):
  venues = []
  try:
    #get distinct cities 
    distinct_cities = set([(venue.city, venue.state) for venue in venues_raw])
    #prepare data
    for city,state in distinct_cities:
      venue_dict = {'city':city, 'state': state, 'venues':[]}
      venues_in_city = [{'id': venue.id,\
                         'name': venue.name,\
                         'num_upcoming_shows': len(venue.get_future_shows())}\
                         for venue in venues_raw\
                         if venue.city==city and venue.state==state]
      venue_dict['venues'] = venues_in_city
      venues.append(venue_dict)
  except Exception as e:
    raise e
  return venues

def get_artists(artists_raw):
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
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
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
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response={
    "count": 1,
    "data": [{
      "id": 2,
      "name": "The Dueling Pianos Bar",
      "num_upcoming_shows": 0,
    }]
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
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
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
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
    created = venue.create(genres)
    if created:
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
    print("Error while creating new venue: ", e)
    print(traceback.format_exc())
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    abort(500)
  
  
 
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # # on successful db insert, flash success
  # flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # # TODO: on unsuccessful db insert, flash an error instead.
  # # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  result = Artist.query.with_entities(Artist.id,Artist.name).all()
  data = get_artists(result)
  print(data)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  response={
    "count": 1,
    "data": [{
      "id": 4,
      "name": "Guns N Petals",
      "num_upcoming_shows": 0,
    }]
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  try:
    result = Artist.query.filter_by(id=artist_id).all()
    print(result)
    if len(result) == 0:
      print("No result for found for artist id {}".format(artist_id))
      abort(404) 
    data = result[0].format_all()
    print(data)
    return render_template('pages/show_artist.html', artist=data)
  except Exception as e:
    print("Error occured while fetching artist", e)
    print(traceback.format_exc())
    abort(500)
  

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data=[{
    "venue_id": 1,
    "venue_name": "The Musical Hop",
    "artist_id": 4,
    "artist_name": "Guns N Petals",
    "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "start_time": "2019-05-21 21:30:00.000"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 5,
    "artist_name": "Matt Quevedo",
    "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "start_time": "2019-06-15 23:00:00.000"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-01 20:00:00.000"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-08 20:00:00.000"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-15 20:00:00.000"
  }]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  print(request.get_data())
  print(request.form)
  sample = request.form.to_dict()
  print(sample)
  print(type(sample))
  print(sample['start_time'])

  # on successful db insert, flash success
  flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

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

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
