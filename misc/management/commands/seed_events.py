import os
import re
import tempfile
import logging
import time
from datetime import datetime, timedelta

import requests
from PIL import Image, ImageDraw, ImageFont

from django.core.management.base import BaseCommand
from django.core.files import File
from django.utils import timezone
from django.utils.text import slugify

from misc.models import Event  # adjust import to your app/model path

logger = logging.getLogger(__name__)


# --------------------------
events_data = [
    # August 2025 (from 10th)
    {
        'title': 'Kajari Teej',
        'description': 'Kajari Teej observed as per Hindu Panchang.',
        'event_date': '2025-08-11',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Navratri_Navaratri_Dasara_Dussehra_festival_images_and_celebrations_collage.jpg'
    },
    {
        'title': 'Heramba Sankashti',
        'description': 'Heramba Sankashti vrat.',
        'event_date': '2025-08-11',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Vijayadashami_01.jpg'
    },
    {
        'title': 'Bahula Chaturthi',
        'description': 'Bahula Chaturthi observance.',
        'event_date': '2025-08-12',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Temple/Home', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Chhath_Pooja.jpg'
    },
    {
        'title': 'Nag Panchami',
        'description': 'Nag Panchami festival',
        'event_date': '2025-08-13',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Chhath_Pooja.jpg'
    },
    {
        'title': 'Randhan Chhath',
        'description': 'Randhan Chhath observance',
        'event_date': '2025-08-13',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Chhath_Pooja.jpg'
    },
    {
        'title': 'Balarama Jayanti',
        'description': 'Birth anniversary of Balarama.',
        'event_date': '2025-08-14',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Janmashtami_celebration_04.jpg'
    },
    {
        'title': 'Shitala Satam',
        'description': 'Shitala Satam fasting day.',
        'event_date': '2025-08-14',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Navratri_Navaratri_dasara_festival_images_and_celebrations_collage.jpg'
    },
    {
        'title': 'Janmashtami (Smarta)',
        'description': 'Krishna Janmashtami (Smarta).',
        'event_date': '2025-08-15',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Krishna_janmashtami_%281%29.jpg'
    },
    {
        'title': 'Janmashtami (ISKCON)',
        'description': 'Krishna Janmashtami (ISKCON Midnight celebration).',
        'event_date': '2025-08-16',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Temple complex', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Janmashtami_celebration_04.jpg'
    },
    {
        'title': 'Dahi Handi',
        'description': 'Dahi Handi festive event.',
        'event_date': '2025-08-16',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Community grounds', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Janmashtami_fesitval.jpg'
    },
    {
        'title': 'Simha Sankranti',
        'description': 'Sun’s transition into Leo (Simha Sankranti).',
        'event_date': '2025-08-16',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Navratri_Navaratri_festival_preparations_and_performance_arts_collage.jpg'
    },
    {
        'title': 'Malayalam New Year (Chingam 1)',
        'description': 'Malayalam New Year (Chingam 1).',
        'event_date': '2025-08-16',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Dev_Deepavali\'_celebrations_in_Varanasi_on_Karthik_Purnima..jpg'
    },
    {
        'title': 'Rohini Vrat',
        'description': 'Rohini Vrat fasting day.',
        'event_date': '2025-08-17',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Navratri_Navaratri_dasara_festival_images_and_celebrations_collage.jpg'
    },
    {
        'title': 'Aja Ekadashi',
        'description': 'Aja Ekadashi observance.',
        'event_date': '2025-08-18',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Navratri_Navaratri_preparations_and_performance_arts_collage.jpg'
    },
    {
        'title': 'Paryushana Parva begins',
        'description': 'Start of Paryushana Parva (Jain festival).',
        'event_date': '2025-08-20',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Ganesh_Chaturthi_4.jpg'
    },
    {
        'title': 'Budha Pradosh Vrat',
        'description': 'Budha Pradosh Vrat fasting.',
        'event_date': '2025-08-20',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Ganesh_Chaturthi_4.jpg'
    },
    {
        'title': 'Masik Shivaratri',
        'description': 'Monthly Shivaratri observance.',
        'event_date': '2025-08-20',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Ganesh_Chaturthi_4.jpg'
    },
    {
        'title': 'Pithori Amavasya',
        'description': 'Pithori Amavasya observance.',
        'event_date': '2025-08-22',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Chhath_Pooja.jpg'
    },
    {
        'title': 'Hartalika Teej',
        'description': 'Hartalika Teej festival.',
        'event_date': '2025-08-25',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Navratri_Navaratri_Dasara_festival_images_and_celebrations_collage.jpg'
    },
    {
        'title': 'Ganesh Chaturthi',
        'description': 'Celebration of Lord Ganesha’s birthday.',
        'event_date': '2025-08-26',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Ganesh_Chaturthi_4.jpg'
    },
    {
        'title': 'Rishi Panchami',
        'description': 'Rishi Panchami observance.',
        'event_date': '2025-08-27',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Navratri_Navaratri_festival_preparations_and_performance_arts_collage.jpg'
    },
    {
        'title': 'Mahalakshmi Vrat begins',
        'description': 'Begin of Mahalakshmi Vrat.',
        'event_date': '2025-08-30',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Diwali_1201.jpg'
    },
    {
        'title': 'Radha Ashtami',
        'description': 'Radha Ashtami observance.',
        'event_date': '2025-08-31',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Janmashtami_celebration_04.jpg'
    },

    # September 2025 (complete)
    {
        'title': 'Parsva Ekadashi',
        'description': 'Parsva Ekadashi observance.',
        'event_date': '2025-09-03',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Vijayadashami_01.jpg'
    },
    {
        'title': 'Vamana Jayanti',
        'description': 'Vamana Jayanti festival.',
        'event_date': '2025-09-04',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Navratri_Navaratri_Dasara_festival_images_and_celebrations_collage.jpg'
    },
    {
        'title': 'Onam',
        'description': 'Onam harvest festival.',
        'event_date': '2025-09-05',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Dev_Deepavali\'_celebrations_in_Varanasi_on_Karthik_Purnima..jpg'
    },
    {
        'title': 'Ganesh Visarjan',
        'description': 'Ganesh Visarjan ceremony.',
        'event_date': '2025-09-06',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Riverbank', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Ganesh_Chaturthi_4.jpg'
    },
    {
        'title': 'Anant Chaturdashi',
        'description': 'Anant Chaturdashi observance.',
        'event_date': '2025-09-06',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Vijayadashami_01.jpg'
    },
    {
        'title': 'Bhadrapada Purnima',
        'description': 'Bhadrapada Purnima fasting.',
        'event_date': '2025-09-07',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Dev_Deepavali\'_celebrations_in_Varanasi_on_Karthik_Purnima..jpg'
    },
    {
        'title': 'Vishwakarma Puja',
        'description': 'Worship of Vishwakarma, the divine architect.',
        'event_date': '2025-09-16',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Workshops/Factories', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Navratri_Navaratri_Dasara_festival_images_and_celebrations_collage.jpg'
    },
    {
        'title': 'Indira Ekadashi',
        'description': 'Indira Ekadashi fasting.',
        'event_date': '2025-09-17',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Ganesh_Chaturthi_4.jpg'
    },
    {
        'title': 'Sarva Pitru Amavasya',
        'description': 'Day for honoring ancestors (Sarvapitru Amavasya).',
        'event_date': '2025-09-21',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Ghat/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Dev_Deepavali\'_celebrations_in_Varanasi_on_Karthik_Purnima..jpg'
    },
    {
        'title': 'Navratri Begins',
        'description': 'Start of Shardiya Navratri.',
        'event_date': '2025-09-22',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Navratri_Navaratri_Dasara_festival_images_and_celebrations_collage.jpg'
    },
    {
        'title': 'Durga Ashtami',
        'description': 'Durga Ashtami Puja rituals.',
        'event_date': '2025-09-30',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Navratri_Navaratri_Dasara_festival_images_and_celebrations_collage.jpg'
    },
    {
        'title': 'Maha Navami',
        'description': 'Maha Navami concluding Navratri.',
        'event_date': '2025-09-30',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Vijaya_Dashami_day_in_Tollygunge_area_Kolkata_Durga_Puja_2022_05.jpg'
    },

    # October 2025
    {
        'title': 'Vijayadashami (Dussehra)',
        'description': 'Victory of good over evil—Vijayadashami.',
        'event_date': '2025-10-02',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Public Grounds', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Vijayadashami_01.jpg'
    },
    {
        'title': 'Papankusha Ekadashi',
        'description': 'Papankusha Ekadashi fasting.',
        'event_date': '2025-10-03',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Navratri_Navaratri_festival_preparations_and_performance_arts_collage.jpg'
    },
    {
        'title': 'Kojagara Puja (Sharad Purnima)',
        'description': 'Sharad Purnima (Kojagara Puja).',
        'event_date': '2025-10-06',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Dev_Deepavali\'_celebrations_in_Varanasi_on_Karthik_Purnima..jpg'
    },
    {
        'title': 'Karwa Chauth',
        'description': 'Karwa Chauth fasting for spouses.',
        'event_date': '2025-10-09',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Ganesh_Chaturthi_4.jpg'
    },
    {
        'title': 'Rama Ekadashi',
        'description': 'Rama Ekadashi fasting day.',
        'event_date': '2025-10-16',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Navratri_Navaratri_festival_preparations_and_performance_arts_collage.jpg'
    },
    {
        'title': 'Tula Sankranti',
        'description': 'Sun’s transit into Libra (Tula Sankranti).',
        'event_date': '2025-10-17',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Navratri_Navaratri_festival_preparations_and_performance_arts_collage.jpg'
    },
    {
        'title': 'Dhanteras',
        'description': 'Dhanteras—auspicious start of Diwali.',
        'event_date': '2025-10-18',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Market', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Diwali_1201.jpg'
    },
    {
        'title': 'Narak Chaturdashi',
        'description': 'Narak Chaturdashi festival.',
        'event_date': '2025-10-19',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Diwali_1201.jpg'
    },
    {
        'title': 'Lakshmi Puja (Diwali)',
        'description': 'Festival of Lights—Lakshmi Puja.',
        'event_date': '2025-10-20',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': True,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Diwali_1201.jpg'
    },
    {
        'title': 'Govardhan Puja',
        'description': 'Govardhan Puja celebrations.',
        'event_date': '2025-10-21',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Ganesh_Chaturthi_4.jpg'
    },
    {
        'title': 'Bhai Dooj',
        'description': 'Bhai Dooj—siblings’ celebration.',
        'event_date': '2025-10-22',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Ganesh_Chaturthi_4.jpg'
    },
    {
        'title': 'Chhath Puja',
        'description': 'Sun-worship ceremony of Chhath.',
        'event_date': '2025-10-27',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'River Bank', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Celebrating_Chhath_Puja.jpg'
    },
    {
        'title': 'Kansa Vadh',
        'description': 'Defeat of Kansa by Lord Krishna.',
        'event_date': '2025-10-31',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Krishna_janmashtami_%281%29.jpg'
    },

    # November 2025
    {
        'title': 'Devutthana Ekadashi',
        'description': 'Devutthana Ekadashi observance.',
        'event_date': '2025-11-01',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Ganesh_Chaturthi_4.jpg'
    },
    {
        'title': 'Tulasi Vivah',
        'description': 'Ceremony of Tulasi Vivah.',
        'event_date': '2025-11-02',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Ganesh_Chaturthi_4.jpg'
    },
    {
        'title': 'Kartik Purnima (Dev Deepavali)',
        'description': 'Dev Deepavali lights on Ganga ghats.',
        'event_date': '2025-11-05',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Ganges River', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': True,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Dev_Deepavali\'_celebrations_in_Varanasi_on_Karthik_Purnima..jpg'
    },
    {
        'title': 'Kalabhairav Jayanti',
        'description': 'Kalabhairav Jayanti observance.',
        'event_date': '2025-11-11',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Navratri_Navaratri_Dasara_festival_images_and_celebrations_collage.jpg'
    },
    {
        'title': 'Utpanna Ekadashi',
        'description': 'Utpanna Ekadashi fasting.',
        'event_date': '2025-11-15',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Ganesh_Chaturthi_4.jpg'
    },
    {
        'title': 'Vrishchika Sankranti',
        'description': 'Sun’s transit into Scorpio (Vrishchika Sankranti).',
        'event_date': '2025-11-16',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Navratri_Navaratri_preparations_and_performance_arts_collage.jpg'
    },
    {
        'title': 'Vivah Panchami',
        'description': 'Celebration of Rama–Sita wedding.',
        'event_date': '2025-11-25',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Vijayadashami_01.jpg'
    },
    {
        'title': 'Gita Jayanti / Mokshada Ekadashi',
        'description': 'Gita Jayanti and Mokshada Ekadashi.',
        'event_date': '2025-11-30',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Dev_Deepavali\'_celebrations_in_Varanasi_on_Karthik_Purnima..jpg'
    },

    # December 2025
    {
        'title': 'Mokshada Ekadashi',
        'description': 'Mokshada Ekadashi fasting.',
        'event_date': '2025-12-01',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Dev_Deepavali\'_celebrations_in_Varanasi_on_Karthik_Purnima..jpg'
    },
    {
        'title': 'Margashirsha Purnima',
        'description': 'Margashirsha Purnima observance.',
        'event_date': '2025-12-04',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Dev_Deepavali\'_celebrations_in_Varanasi_on_Karthik_Purnima..jpg'
    },
    {
        'title': 'Dhanu Sankranti',
        'description': 'Sun’s transit into Sagittarius (Dhanu Sankranti).',
        'event_date': '2025-12-15',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Navratri_Navaratri_festival_preparations_and_performance_arts_collage.jpg'
    },
    {
        'title': 'Pausha Putrada Ekadashi',
        'description': 'Ekadashi for welfare of children.',
        'event_date': '2025-12-30',
        'start_time': '00:00', 'end_time': '23:59',
        'location': 'Home/Temple', 'registration_link': '',
        'status': 'PUBLISHED', 'is_featured': False,
        'image_url': 'https://commons.wikimedia.org/wiki/File:Dev_Deepavali\'_celebrations_in_Varanasi_on_Karthik_Purnima..jpg'
    },
]

# --------------------------

def create_enhanced_sample_image(title, color=(255, 140, 0), text_overlay="Event"):
    """Create a fallback image (same as your existing generator)."""
    img = Image.new('RGB', (1200, 800), color=color)
    draw = ImageDraw.Draw(img)
    for i in range(img.height):
        r, g, b = color
        factor = i / img.height
        new_r = int(r * (1 - factor * 0.3))
        new_g = int(g * (1 - factor * 0.3))
        new_b = int(b * (1 - factor * 0.3))
        draw.line([(0, i), (img.width, i)], fill=(new_r, new_g, new_b))

    border_color = (255, 255, 255) if sum(color) < 400 else (0, 0, 0)
    draw.rectangle([20, 20, img.width - 20, img.height - 20], outline=border_color, width=8)
    draw.rectangle([40, 40, img.width - 40, img.height - 40], outline=border_color, width=4)

    try:
        font_size = 72
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
        text_lines = text_overlay.split('\n')
        total_height = len(text_lines) * font_size
        start_y = (img.height - total_height) // 2
        for i, line in enumerate(text_lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (img.width - text_width) // 2
            y = start_y + (i * font_size)
            shadow_color = (0, 0, 0) if sum(color) > 400 else (255, 255, 255)
            draw.text((x + 3, y + 3), line, font=font, fill=shadow_color)
            text_color = (255, 255, 255) if sum(color) < 400 else (0, 0, 0)
            draw.text((x, y), line, font=font, fill=text_color)
    except Exception as e:
        logger.warning(f"Could not add text overlay: {e}")
    return img


def resolve_wikimedia_direct_image_url(page_url):
    """If user passed a Wikimedia Commons page URL (not direct image), fetch page and extract og:image."""
    try:
        r = requests.get(page_url, timeout=10)
        if not r.ok:
            return page_url
        html = r.text
        # try meta property og:image
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if m:
            return m.group(1)
        # try other meta name variants
        m = re.search(r'<meta[^>]+name=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if m:
            return m.group(1)
    except Exception as e:
        logger.warning(f"resolve_wikimedia_direct_image_url error for {page_url}: {e}")
    return page_url


def download_image_to_temp(url, filename_hint):
    """
    Downloads image (resolves Wikimedia pages), returns temp file path and filename to use.
    Raises exception on failure.
    """
    try:
        # resolve wikimedia file pages to actual image url
        if "commons.wikimedia.org/wiki/File:" in url:
            url = resolve_wikimedia_direct_image_url(url)

        resp = requests.get(url, stream=True, timeout=15)
        resp.raise_for_status()

        # try to determine extension
        ext = ''
        content_type = resp.headers.get('content-type', '')
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = '.jpg'
        elif 'png' in content_type:
            ext = '.png'
        else:
            # fallback from url path
            path = requests.utils.urlparse(url).path
            if '.' in path:
                ext = os.path.splitext(path)[1]
            else:
                ext = '.jpg'

        safe_name = slugify(filename_hint)[:40] or 'image'
        tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        for chunk in resp.iter_content(1024):
            tmp.write(chunk)
        tmp.flush()
        tmp.close()
        return tmp.name, f"{safe_name}{ext}"
    except Exception as e:
        raise


class Command(BaseCommand):
    help = 'Seed test data for Events (with image download, fallback to generated image)'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing events before seeding')

    def handle(self, *args, **options):
        if options.get('clear'):
            Event.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared all existing events'))

        self.stdout.write(self.style.SUCCESS(f'🌱 Starting Hindu Festival Seeding with ImageKit Integration...'))
        self.stdout.write(self.style.SUCCESS(f'📅 Creating {len(events_data)} festivals from Aug 10 to Dec 31, 2025'))
        
        created = []
        featured_count = 0
        
        for i, event_data in enumerate(events_data):
            self.stdout.write(f"📝 Creating festival {i+1}/{len(events_data)}: {event_data.get('title')}")
            temp_paths = []
            
            # Make some major festivals featured
            major_festivals = ['Ganesh Chaturthi', 'Diwali', 'Dussehra', 'Janmashtami', 'Navratri', 'Karva Chauth', 'Dhanteras']
            if any(festival in event_data.get('title', '') for festival in major_festivals) and featured_count < 10:
                event_data['is_featured'] = True
                featured_count += 1
            
            try:
                # Prepare event_date (supports string or date)
                if isinstance(event_data['event_date'], str):
                    event_date = datetime.strptime(event_data['event_date'], '%Y-%m-%d').date()
                else:
                    event_date = event_data['event_date']

                # Create enhanced festival image (no external downloads to avoid issues)
                self.stdout.write(f"📤 Creating festival image and uploading to ImageKit.io...")
                img = create_enhanced_sample_image(event_data.get('title', 'Festival'))
                
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    img.save(tmp, format='JPEG', quality=90, optimize=True)
                    tmp_path = tmp.name
                    temp_paths.append(tmp_path)
                
                with open(tmp_path, 'rb') as f:
                    image_file = File(f, name=f"{slugify(event_data.get('title','festival'))}.jpg")
                    
                    # Create event with the image file - ImageKit upload happens in model save()
                    event = Event.objects.create(
                        title=event_data['title'],
                        description=event_data['description'],
                        event_date=event_date,
                        start_time=event_data.get('start_time', '00:00'),
                        end_time=event_data.get('end_time', '23:59'),
                        location=event_data.get('location', ''),
                        registration_link=event_data.get('registration_link', ''),
                        status=event_data.get('status', 'PUBLISHED'),
                        is_featured=event_data.get('is_featured', False),
                        original_image=image_file
                    )
                    created.append(event)
                    
                    # Check if ImageKit URLs were generated
                    imagekit_status = "🌐 ImageKit" if event.imagekit_original_url else "💾 Local"
                    featured_status = "⭐" if event.is_featured else "📅"
                    status_color = {"PUBLISHED": "🟢", "DRAFT": "🟡", "ARCHIVED": "🔴"}.get(event.status, '❓')
                    
                    self.stdout.write(self.style.SUCCESS(f"✅ Festival created: {event.title} (ID: {event.id})"))
                    
                    # Show ImageKit URLs if generated
                    if event.imagekit_original_url:
                        self.stdout.write(self.style.SUCCESS(f"🌐 ImageKit URLs generated successfully!"))
                        self.stdout.write(f"   📸 Original: {event.imagekit_original_url[:60]}...")
                        if event.imagekit_thumbnail_url:
                            self.stdout.write(f"   🖼️  Thumbnail: {event.imagekit_thumbnail_url[:60]}...")
                        if event.imagekit_banner_url:
                            self.stdout.write(f"   📊 Banner: {event.imagekit_banner_url[:60]}...")
                    
                    # Small delay to avoid overwhelming ImageKit API
                    if (i + 1) % 5 == 0:  # Every 5 events
                        self.stdout.write(f"⏱️  Brief pause to avoid API rate limits...")
                        time.sleep(2)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error creating festival {event_data.get('title')}: {e}"))
                logger.exception(e)
            finally:
                # cleanup temp files
                for p in temp_paths:
                    try:
                        os.unlink(p)
                    except:
                        pass

        # Final summary
        self.stdout.write(self.style.SUCCESS(f"\n" + "="*60))
        self.stdout.write(self.style.SUCCESS(f"🎉 Successfully created {len(created)} Hindu festivals with ImageKit integration!"))
        
        # Show festival summary
        self.stdout.write(self.style.SUCCESS(f"\n📋 Created Festivals Summary:"))
        for event in created[:10]:  # Show first 10
            imagekit_status = "🌐" if event.imagekit_original_url else "💾"
            featured_status = "⭐" if event.is_featured else "📅"  
            status_color = {"PUBLISHED": "🟢", "DRAFT": "🟡", "ARCHIVED": "🔴"}.get(event.status, '❓')
            
            self.stdout.write(f"   {status_color}{featured_status}{imagekit_status} ID: {event.id} | {event.title} | {event.slug}")
        
        if len(created) > 10:
            self.stdout.write(f"   ... and {len(created) - 10} more festivals")
        
        # Statistics
        published_count = sum(1 for e in created if e.status == 'PUBLISHED')
        featured_count = sum(1 for e in created if e.is_featured)
        imagekit_count = sum(1 for e in created if e.imagekit_original_url)
        
        self.stdout.write(self.style.SUCCESS(f"\n📊 Festival Statistics:"))
        self.stdout.write(f"   📅 Total Festivals: {len(created)}")
        self.stdout.write(f"   🟢 Published: {published_count}")
        self.stdout.write(f"   ⭐ Featured: {featured_count}")
        self.stdout.write(f"   🌐 ImageKit Integration: {imagekit_count}/{len(created)}")
        
        self.stdout.write(self.style.SUCCESS(f"\n✨ Hindu Festival seeding completed! Events ready for testing with ImageKit.io integration."))

        return
