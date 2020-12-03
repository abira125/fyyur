from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
from datetime import datetime
import traceback
from constants import FUTURE, PAST


def setup_db(app):
    db.app = app
    db.init_app(app)
    db.create_all()

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

#------------------------------------------------
# Venue Model

class Venue(db.Model):
    """
    Model for Venue
    """
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
    genres = db.relationship("VenueGenre", backref=db.backref('venues', lazy=True), passive_deletes=True) # passive_deletes to go with ON DELETE CASCADE, see VenueGenres class

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
    
    def get_shows(self, tense):
      """
      Iterates through the list of shows related to this venue and gets the future show details using backref
      tense

      Parameters:
        tense (str): denotes whether the details are required for future or past shows

      Returns:
        shows(list): shows with details about start_time and artists 
      """
      shows = []
      shows_raw = []
      try:
        if tense == FUTURE:
          shows_raw = list(filter(lambda x: x.start_time > datetime.now(), self.shows))
        elif tense == PAST:
          shows_raw = list(filter(lambda x: x.start_time < datetime.now(), self.shows))
        else:
          raise ValueError("Invalid tense for shows")
        for show in shows_raw:
          shows.append({'artist_id': show.artists.id,\
                        'artist_name': show.artists.name,\
                        'artist_image_link': show.artists.image_link,\
                        'start_time': show.start_time.isoformat()})  
      except Exception as e:
        raise e      
      return shows
      
    
    def get_genres(self):
      """
      Get genre names for the associated genres
      """
      genres = []
      try:
        genres = [genre.name for genre in self.genres]
      except Exception as e:
        raise e
      return genres

    
    def format_all(self):
      """
      Format or prepare data as per the requirement
      """
      venue_dict = {}
      try:
        upcoming_shows = self.get_shows(FUTURE)
        past_shows = self.get_shows(PAST)
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
      """
      Create a Venue resource and persist to DB
      """
      try:
        for genre in genres:
          vg = VenueGenre(name=genre)
          self.genres.append(vg)
        db.session.add(self)
        db.session.commit()
      except Exception as e:
        db.session.rollback()
        raise e
      finally:
        db.session.close()



#------------------------------------------------
# Show Model

class Show(db.Model): 
    """
    Show model associating Venue and Artist model using association object pattern
    """
    __tablename__ = 'show'

    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id', ondelete='CASCADE'), primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id', ondelete='CASCADE'), primary_key=True)
    start_time = db.Column(db.DateTime, primary_key=True)
    artists = db.relationship('Artist', backref=db.backref('shows', lazy=True))

    def __init__(self, venue_id, artist_id, start_time):
      self.venue_id = venue_id
      self.artist_id = artist_id
      self.start_time = start_time
      
    def get_show_dict(self):
      """
      Prepares show dictionary for get endpoint
      """
      show_dict = {}
      try:
        show_dict = {
          "venue_id": self.venue_id,
          "venue_name": self.venues.name,
          "artist_id": self.artist_id,
          "artist_name": self.artists.name,
          "artist_image_link": self.artists.image_link,
          "start_time": self.start_time.isoformat() 
        }
      except Exception as e:
        raise e
      return show_dict

    def create(self):
      """
      Creates a show and persists to DB
      """
      try:
        db.session.add(self)
        db.session.commit()
      except Exception as e:
        db.session.rollback()
        raise e
      finally:
        db.session.close()


#------------------------------------------------
# Artist Model

class Artist(db.Model):
    """
    Artist model
    """
    
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
    genres = db.relationship("ArtistGenre", backref=db.backref('artists', lazy=True), passive_deletes=True)

    def __init__(self, name, city, state, phone, facebook_link,\
                 website_link, image_link, seeking_venue, seeking_description):
      self.name = name
      self.city = city
      self.state = state
      self.phone = phone
      self.facebook_link = facebook_link
      self.website_link = website_link
      self.image_link = image_link
      self.seeking_venue = seeking_venue
      self.seeking_description = seeking_description

    def get_shows(self, tense):
      """
      Iterates through the list of shows related to this venue and gets the future show details using backref
      tense

      Parameters:
        tense (str): denotes whether the details are required for future or past shows

      Returns:
        shows(list): shows with details about start_time and venues
      """
      shows = []
      shows_raw = []
      try:
        if tense == FUTURE:
          shows_raw = list(filter(lambda x: x.start_time > datetime.now(), self.shows))
        elif tense == PAST:
          shows_raw = list(filter(lambda x: x.start_time < datetime.now(), self.shows))
        else:
          raise ValueError("Invalid tense for shows")
        for show in shows_raw:
          shows.append({'venue_id': show.venues.id,\
                        'venue_name': show.venues.name,\
                        'venue_image_link': show.venues.image_link,\
                        'start_time': show.start_time.isoformat()})  
      except Exception as e:
        raise e      
      return shows 

  
    def get_genres(self):
      """
      Get associated genre names 
      """
      genres = []
      try:
        genres = [genre.name for genre in self.genres]
      except Exception as e:
        raise e
      return genres 

    def format_all(self):
      """
      Format or prepare data as per the requirement
      """
      artist_dict = {}
      try:
        upcoming_shows, past_shows = self.get_shows(FUTURE), self.get_shows(PAST)
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

    def create(self, genres):
      """
      Create resource for artist and persist
      """
      try:
        for genre in genres:
          ag = ArtistGenre(name=genre)
          self.genres.append(ag)
        db.session.add(self)
        db.session.commit()
      except Exception as e:
        db.session.rollback()
        raise e
      finally:
        db.session.close()

#------------------------------------------------
# VenueGenre Model
class VenueGenre(db.Model):
    """
    VenueGenres model stores genres for Venues. This was necessary to maintain first normal form. The relationship between Venue and Genre has been modelled as a one to many relationship   
    """
    # TODO: Model the relationship between Venue and Genre as a many to many relationship
    __tablename__ = 'venuegenre'
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id', ondelete='CASCADE'), primary_key=True) # ondelete='CASCADE' preferred over ORM based delete cascade as this is native to db
    name = db.Column(db.String(30), nullable=False, primary_key=True)

#------------------------------------------------
# ArtistGenre Model
class ArtistGenre(db.Model):
    """
    ArtistGenres model stores genres for Artists. This was necessary to maintain first normal form. The relationship between Aritist and Genre has been modelled as a one to many relationship   
    """
    # TODO: Model the relationship between Artist and Genre as a many to many relationship
    __tablename__ = 'artistgenre'
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id', ondelete='CASCADE'), primary_key=True)
    name = db.Column(db.String(30), nullable=False, primary_key=True)
