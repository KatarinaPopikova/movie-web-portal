import copy
import os
import json
from pytube import YouTube
from ultralytics import YOLO
from yolov7.detect import detect_main, find_labels


class DetectMovies:
    @classmethod
    def detect_yolov8(cls, posters_links, movie_ids, categories, confidence):
        print("Start detection on posters yolov8.")
        model = YOLO()
        # model_custom = YOLO("customModel")
        names_coco = [value for value in model.names.values()]
        print(names_coco)
        # names_custom = model.names

        intersection_categories_coco = set(names_coco) & set(categories)
        # intersection_categories_custom = set(names_custom) & set(categories)
        intersection_categories_custom = []
        if len(intersection_categories_coco):
            results = model.predict(source=posters_links, conf=confidence, device='cpu')
        if len(intersection_categories_custom):
            results_custom = model_custom.predict(source=posters_links, conf=confidence, device=0)

        detection = []

        for index in range(len(movie_ids)):
            current_img = {
                "poster_path": posters_links[index],
                "id": movie_ids[index],
                "det": []
            }

            if len(intersection_categories_coco):
                coco_det = cls.process_detection(results[index], intersection_categories_coco)
                if not coco_det:
                    continue
                current_img["det"] += coco_det

            if len(intersection_categories_custom):
                custom_det = cls.process_detection(results_custom[index], intersection_categories_custom)
                if not current_img:
                    continue
                current_img["det"] += custom_det

            detection.append(current_img)

        if detection:
            detection = sorted(detection, key=lambda x: (max(image_det['conf'] for image_det in x['det'])),
                               reverse=True)

        print("Detection finished.")

        return detection

    @classmethod
    def process_detection(cls, result, categories):
        names = result.names
        detections = []
        if result is not None:
            must_detect_categories = copy.deepcopy(categories)

            for box in reversed(result.boxes):
                xywh = box.xywhn.squeeze()
                category = box.cls.squeeze()
                conf = box.conf.squeeze()
                if names[int(category)] in categories:
                    if names[int(category)] in must_detect_categories:
                        must_detect_categories.remove(names[int(category)])

                    detections.append({
                        "label": names[int(category)],
                        "box": xywh.tolist(),
                        "conf": float(conf)
                    })

            if len(must_detect_categories) == 0:
                return detections
        return []

    @classmethod
    def make_trailer_detection(cls, movie_dict_with_links, categories):
        print("Start detection on trailers yolov8.")

        movie_with_searching_objects = []

        model = YOLO()
        # model_custom = YOLO("customModel")
        names_coco = [value for value in model.names.values()]
        # names_custom = model.names

        intersection_categories_coco = set(names_coco) & set(categories)
        # intersection_categories_custom = set(names_custom) & set(categories)
        intersection_categories_custom = []

        for movie_result in movie_dict_with_links:
            youtube_object = YouTube(movie_result['trailer_link'])
            youtube_object = youtube_object.streams.get_highest_resolution()
            try:
                youtube_object.download(output_path='trailers', filename=str(movie_result['id']) + '.mp4')
            except:
                print("An error has occurred: " + str(movie_result['id']))

            print("Download is completed successfully")

            source = 'trailers/' + str(movie_result['id']) + '.mp4'
            if len(intersection_categories_coco):
                results = model.predict(source=source, device=0, vid_stride=5, verbose=False, imgsz=192)
                all_objects = cls.get_all_objects_with_best_conf(results)
                objects = cls.contains_all_searching_objects(all_objects, intersection_categories_coco)
                if not objects:
                    continue
                movie_result["objects"] += objects
            if len(intersection_categories_custom):
                results_custom = model_custom.predict(source=source, device=0, vid_stride=5, verbose=False, imgsz=192)
                all_objects = cls.get_all_objects_with_best_conf(results_custom)
                objects = cls.contains_all_searching_objects(all_objects, intersection_categories_custom)
                if not objects:
                    continue
                movie_result["objects"] += objects

            os.remove(source)

            if movie_result["objects"]:
                movie_with_searching_objects.append(movie_result)

        print("Detection finished.")

        return movie_with_searching_objects

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

        return [{'object': name, 'conf': conf} for name, conf in name_to_conf.items()]

    @classmethod
    def contains_all_searching_objects(cls, objects_in_video, categories):
        searching_categories = list(filter(lambda obj: obj['object'] in categories, objects_in_video))
        return searching_categories if len(searching_categories) == len(categories) else None

    @classmethod
    def make_detection(cls, categories):
        return len(categories) > 0

    @classmethod
    def detect_yolov7(self, links, movie_ids, categories, confidence):
        return detect_main(links, movie_ids, categories, confidence)

    @classmethod
    def find_labels(cls):
        return find_labels()
