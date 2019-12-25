import time
import numpy as np
import tensorflow as tf
import cv2

# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_CKPT = 'modules/face_identification/faceDetectorMobilenetSSD.pb'


class TensorflowFaceDetector(object):
    def __init__(self):
        """Tensorflow detector
        """

        self.detection_graph = tf.Graph()
        with self.detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')


        with self.detection_graph.as_default():
            config = tf.ConfigProto()
            config.gpu_options.per_process_gpu_memory_fraction = 0.15
            self.sess = tf.Session(graph=self.detection_graph, config=config)
            self.windowNotSet = True


    def run(self, image):

        """image: bgr image
        return (boxes, scores, classes, num_detections)
        """

        image_np = image
        [h, w] = image.shape[:2]
        # the array based representation of the image will be used later in order to prepare the
        # result image with boxes and labels on it.
        # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
        image_np_expanded = np.expand_dims(image_np, axis=0)
        image_tensor = self.detection_graph.get_tensor_by_name('image_tensor:0')
        # Each box represents a part of the image where a particular object was detected.
        boxes = self.detection_graph.get_tensor_by_name('detection_boxes:0')
        # Each score represent how level of confidence for each of the objects.
        # Score is shown on the result image, together with the class label.
        scores = self.detection_graph.get_tensor_by_name('detection_scores:0')
        classes = self.detection_graph.get_tensor_by_name('detection_classes:0')
        num_detections = self.detection_graph.get_tensor_by_name('num_detections:0')
        # Actual detection.
        start_time = time.time()
        (boxes, scores, classes, num_detections) = self.sess.run(
            [boxes, scores, classes, num_detections],
            feed_dict={image_tensor: image_np_expanded})
        boxes = np.squeeze(boxes)
        scores = np.squeeze(scores)
        max_boxes_to_draw = boxes.shape[0]
        array = []

        for i in range(min(max_boxes_to_draw, boxes.shape[0])):
            if scores[i] > 0.65:
                box = tuple(boxes[i].tolist())
                ymin, xmin, ymax, xmax = box
                xmax = int(xmax * w)
                xmin = int(xmin * w)
                ymax = int(ymax * h)
                ymin = int(ymin * h)

                array.append([ymin, xmax, ymax, xmin])
        return array

    def draw_rectangle(self, frame, rectangle, color, thickness, label=None):
        if rectangle is not None:

            bot = (rectangle[1],rectangle[2])
            top = (rectangle[3],rectangle[0])
            
            cv2.rectangle(frame, top, bot, color, thickness)

            if label is not None:
                cv2.putText(frame, label, top, cv2.FONT_HERSHEY_SIMPLEX, 2, (255,0,0), 2)

        return frame
