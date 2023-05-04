import copy
import os
import time
import torch
# torch.cuda.empty_cache()

import cv2
from pytube import YouTube
from ultralytics import YOLO
from yolov7.detect import detect_main, find_labels

from numpy import random


class DetectMovies:
    @classmethod
    def detect_yolov8(cls, posters_links, model_type="nano", movies=None, categories=None, confidence=0.25):

        print("Start detection on posters yolov8.")
        if model_type == "nano":
            model = YOLO()
            model_custom = YOLO("yolov8n_custom.pt")
        else:
            model = YOLO("yolov8l.pt")
            model_custom = YOLO("yolov8l_custom.pt")

        classes_coco = [list(model.names.values()).index(name) for name in
                        set(model.names.values()) & set(categories)] if categories else None
        classes_custom = [list(model_custom.names.values()).index(name) for name in
                          set(model_custom.names.values()) & set(categories)] if categories else None

        det = []

        if not categories or len(classes_coco):
            detection = model.predict(source=posters_links, conf=confidence, device=0, classes=classes_coco,
                                      verbose=False, save=False)
            if movies is None:
                det += cls.process_detection(detection[0], categories, model_type)
            else:
                posters_links, movies = cls.remove_movies_with_no_det(posters_links, movies, detection, classes_coco,
                                                                      model_type)
        if not categories or len(classes_custom):
            detection = model_custom.predict(source=posters_links, conf=confidence, device=0, classes=classes_coco,
                                             verbose=False, save=False)
            if movies is None:
                det += cls.process_detection(detection[0], categories, model_type)
                return det
            else:
                _, movies = cls.remove_movies_with_no_det(posters_links, movies, detection, classes_custom, model_type)

        if movies and categories:
            movies = sorted(movies, key=lambda x: (max(image_det['conf'] for image_det in x['det'])), reverse=True)
        print("Detection finished.")

        return movies

    @classmethod
    def remove_movies_with_no_det(cls, posters_links, movies, detection, categories, model_type):
        new_posters_links = []
        new_movies = []

        for index, poster_link in enumerate(posters_links):
            det = cls.process_detection(detection[index], categories, model_type)
            if det or not categories:
                movies[index]["det"] += det
                new_movies.append(movies[index])
                new_posters_links.append(poster_link)

        return new_posters_links, new_movies

    @classmethod
    def process_detection(cls, result, categories, model_type):
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
                    "model": model_type,
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
        model_custom = YOLO("yolov8n_custom.pt")

        classes_coco = [list(model.names.values()).index(name) for name in
                        set(model.names.values()) & set(categories)] if categories else None
        classes_custom = [list(model_custom.names.values()).index(name) for name in
                          set(model_custom.names.values()) & set(categories)] if categories else None

        for movie_result in movie_dict_with_trailer_links:
            if movie_result['trailer_link']:
                print(movie_result['trailer_link'])
                stream = None
                retries = 0
                while retries < 3:
                    try:
                        youtube_object = YouTube(movie_result['trailer_link'], use_oauth=True, allow_oauth_cache=True)
                        if youtube_object.length > 360:
                            print("Video is longer than 6min: " + str(movie_result['id']))
                            break

                        stream = youtube_object.streams.filter(res='240p').first()
                        if stream is None:
                            print("not 240")
                            stream = youtube_object.streams.get_lowest_resolution()

                        break  # break out of the loop if successful
                    except:
                        print('Error getting stream, retrying in 5 seconds... (' + str(retries + 1) + '/3)')
                        retries += 1
                        time.sleep(5)
                else:  # else block executes only if while loop didn't break
                    print('Failed to get stream after 3 retries, moving on to next movie result...')
                    continue
                try:
                    if stream is None:
                        continue
                    stream.download(output_path='trailers', filename=str(movie_result['id']) + '.mp4')
                except:
                    print("An error has occurred: " + str(movie_result['id']))
                    continue

                print("Download is completed successfully")

                source = 'trailers/' + str(movie_result['id']) + '.mp4'

                if not categories or len(classes_coco):
                    if not cls.process_results(model, source, classes_coco, movie_result, categories, confidence):
                        continue

                if not categories or len(classes_custom):
                    if not cls.process_results(model_custom, source, classes_custom, movie_result, categories,
                                               confidence):
                        continue

                os.remove(source)

            if not categories or movie_result["trailer_objects"]:
                movie_with_searching_objects.append(movie_result)

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

        return [{'model': 'yolov8n', 'label': name, 'conf': conf} for name, conf in name_to_conf.items()]

    @classmethod
    def contains_all_searching_objects(cls, objects_in_video, categories):
        unique_names_of_categories = {objects['label'] for objects in objects_in_video}
        print(unique_names_of_categories)
        return objects_in_video if len(unique_names_of_categories) == len(categories) else None

    @classmethod
    def make_detection(cls, categories):
        return len(categories) > 0

    @classmethod
    def detect_yolov7(self, links, movies=None, categories=None, confidence=0.25):
        return detect_main(links, movies, categories, confidence)

    @classmethod
    def find_labels(cls):
        return find_labels()

    @classmethod
    def detect_and_plot(cls, frame, yolo):
        model = YOLO(yolo)
        detection = model.predict(source=frame, device=0, verbose=False)

        return cls.process_save_detection(detection, frame)

    @classmethod
    def process_save_detection(cls, results, frame):
        names = results[0].names

        colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]
        for result in results:
            if result is not None:

                for box in reversed(result.boxes):
                    xywh = box.xywhn.squeeze()
                    xyxy = box.xyxy.squeeze()
                    category = box.cls.squeeze()
                    label = f'{names[int(category)]} {box.conf.squeeze():.2f}'

                    plot_one_box(xyxy, frame, label=label, color=colors[int(category)], line_thickness=1)

        return frame


def plot_one_box(x, img, color=None, label=None, line_thickness=3):
    # Plots one bounding box on image img
    tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1  # line/font thickness
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 2, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  # filled
        cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 2, [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)
