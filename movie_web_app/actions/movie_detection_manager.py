import copy
import os
import json
from pytube import YouTube
from ultralytics import YOLO
from yolov7.detect import detect_main, find_labels


class DetectMovies:
    @classmethod
    def detect_yolov8(cls, posters_links, movies, model_type, categories=None, confidence=0.25):
        print("Start detection on posters yolov8.")
        if model_type == "nano":
            model = YOLO()
            model_custom = YOLO("yolov8_custom.pt")
        else:
            model = YOLO("yolov8l.pt")
            model_custom = YOLO("yolov8l_custom.pt")

        classes_coco = [list(model.names.values()).index(name) for name in
                        set(model.names.values()) & set(categories)] if categories else None
        classes_custom = [list(model_custom.names.values()).index(name) for name in
                          set(model_custom.names.values()) & set(categories)] if categories else None

        if not categories or len(classes_coco):
            detection = model.predict(source=posters_links, conf=confidence, device=0, classes=classes_coco,
                                      verbose=False)
            posters_links, movies = cls.remove_movies_with_no_det(posters_links, movies, detection, classes_coco)
        if not categories or len(classes_custom):
            detection = model_custom.predict(source=posters_links, conf=confidence, device=0, classes=classes_coco,
                                             verbose=False)
            _, movies = cls.remove_movies_with_no_det(posters_links, movies, detection, classes_custom)

        if movies and categories:
            movies = sorted(movies, key=lambda x: (max(image_det['conf'] for image_det in x['det'])), reverse=True)
        print("Detection finished.")

        return movies

    @classmethod
    def remove_movies_with_no_det(cls, posters_links, movies, detection, categories):
        new_posters_links = []
        new_movies = []

        for index, poster_link in enumerate(posters_links):
            det = cls.process_detection(detection[index], categories)
            if det or not categories:
                movies[index]["det"] += det
                new_movies.append(movies[index])
                new_posters_links.append(poster_link)

        return new_posters_links, new_movies

    @classmethod
    def process_detection(cls, result, categories):
        must_detect_categories = copy.deepcopy(categories) if categories else None
        names = result.names
        detections = []
        if result is not None:

            for box in reversed(result.boxes):
                xywh = box.xywhn.squeeze()
                category = box.cls.squeeze()
                conf = box.conf.squeeze()
                if must_detect_categories and int(category) in must_detect_categories:
                    must_detect_categories.remove(int(category))

                detections.append({
                    "label": names[int(category)],
                    "box": xywh.tolist(),
                    "conf": float(conf)
                })

            if must_detect_categories is None or len(must_detect_categories) == 0:
                return detections
        return []

    @classmethod
    def make_trailer_detection(cls, movie_dict_with_trailer_links, categories=None, confidence=0.25):
        print("Start detection on trailers yolov8.")

        movie_with_searching_objects = []
        model = YOLO()
        model_custom = YOLO("yolov8_custom.pt")

        classes_coco = [list(model.names.values()).index(name) for name in
                        set(model.names.values()) & set(categories)] if categories else None
        classes_custom = [list(model_custom.names.values()).index(name) for name in
                          set(model_custom.names.values()) & set(categories)] if categories else None

        for movie_result in movie_dict_with_trailer_links:
            if movie_result['trailer_link']:
                youtube_object = YouTube(movie_result['trailer_link'])
                youtube_object = youtube_object.streams.get_highest_resolution()
                try:
                    youtube_object.download(output_path='trailers', filename=str(movie_result['id']) + '.mp4')
                except:
                    print("An error has occurred: " + str(movie_result['id']))

                print("Download is completed successfully")

                source = 'trailers/' + str(movie_result['id']) + '.mp4'

                if not categories or len(classes_coco):
                    if not cls.process_results(model, source, classes_coco, movie_result, categories, confidence):
                        continue

                if not categories or len(classes_custom):
                    if not cls.process_results(model_custom, source, classes_custom, movie_result, categories, confidence):
                        continue

                os.remove(source)

            if not categories or movie_result["trailer_objects"]:
                movie_with_searching_objects.append(movie_result)

            break

        print("Detection finished.")

        return movie_with_searching_objects

    @classmethod
    def process_results(cls, model, source, classes, movie_result, categories, confidence):
        results = model.predict(source=source, device=0, vid_stride=5, verbose=False, imgsz=256,
                                classes=classes, conf=confidence)
        all_objects = cls.get_all_objects_with_best_conf(results)
        if not categories and all_objects:
            movie_result["trailer_objects"] += all_objects
        elif categories:
            objects = cls.contains_all_searching_objects(all_objects, classes)
            if not objects:
                return False
            movie_result["trailer_objects"] += objects
        return True

    @classmethod
    def get_all_objects_with_best_conf(cls, results):
        print("Getting all objects and their conf from trailers.")
        names = results[0].names
        name_to_conf = {}

        for result in results:
            if result is not None:
                for box in result.boxes:
                    name = names[int(box.cls)]
                    conf = float(box.conf)
                    if name not in name_to_conf or conf > name_to_conf[name]:
                        name_to_conf[name] = conf

        return [{'label': name, 'conf': conf} for name, conf in name_to_conf.items()]

    @classmethod
    def contains_all_searching_objects(cls, objects_in_video, categories):
        unique_names_of_categories = {objects['label'] for objects in objects_in_video}
        print(unique_names_of_categories)
        return objects_in_video if len(unique_names_of_categories) == len(categories) else None

    @classmethod
    def make_detection(cls, categories):
        return len(categories) > 0

    @classmethod
    def detect_yolov7(self, links, movies, categories=None, confidence=0.25):
        return detect_main(links, movies, categories, confidence)

    @classmethod
    def find_labels(cls):
        return find_labels()
