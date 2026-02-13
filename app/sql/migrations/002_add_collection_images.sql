-- Add image_path column to collections table
-- Migration: 002_add_collection_images
-- Date: 2026-02-10

-- Add the image_path column
ALTER TABLE collections ADD COLUMN image_path TEXT;

-- Assign images to relevant collections
UPDATE collections SET image_path = '/assets/images/collections/Collection – Gilgamesh.jpg' WHERE collection_id = 1;
UPDATE collections SET image_path = '/assets/images/collections/Collection – Esarhaddon''s Superstitions.jpg' WHERE collection_id = 2;
UPDATE collections SET image_path = '/assets/images/collections/Collection – Enuma Elish.jpg' WHERE collection_id = 6;
UPDATE collections SET image_path = '/assets/images/collections/Collection – Flood Stories.jpg' WHERE collection_id = 7;
UPDATE collections SET image_path = '/assets/images/collections/Collection – Descent of Ishtar.jpg' WHERE collection_id = 8;
UPDATE collections SET image_path = '/assets/images/collections/Collection – Hymns & Tavern Songs.jpg' WHERE collection_id = 10;
UPDATE collections SET image_path = '/assets/images/collections/Collection – Love Poetry.jpg' WHERE collection_id = 11;
UPDATE collections SET image_path = '/assets/images/collections/Collection – Complaint Letters.jpg' WHERE collection_id = 12;
UPDATE collections SET image_path = '/assets/images/collections/Collection – Curses & Insults.jpg' WHERE collection_id = 13;
UPDATE collections SET image_path = '/assets/images/collections/Collection – Royal Propaganda.jpg' WHERE collection_id = 17;
UPDATE collections SET image_path = '/assets/images/collections/Collection – School Texts.jpg' WHERE collection_id = 18;
UPDATE collections SET image_path = '/assets/images/collections/Collection – Medical Texts.jpg' WHERE collection_id = 20;
UPDATE collections SET image_path = '/assets/images/collections/Collection – Self Help.jpg' WHERE collection_id = 21;
