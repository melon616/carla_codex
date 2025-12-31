import sys
import os
import glob

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
import random

class SensorProcessor():
    def __init__(self, save_folder):
        self.save_folder = save_folder
        if not os.path.exists(self.save_folder):
            os.makedirs(output_path)

    def CameraCallback(image):
        print(f"image.frame:{image.frame}")
        print(f"image.timestamp:{image.timestamp}")
        return

    def LidarCallback(lidar_data):
        return 


def main():
    # Set path for output
    output_path = ''
    sensor_processor = SensorProcessor(output_path)

    actor_list = []
    sensor_list = []
    try:
        # 1.0 Create client connecting with Simulation Environment.
        client = carla.Client('localhost', 2000)
        client.set_timeout(2.0)
        
        # 2.0 Get SimWorld.
        world = client.get_world()
        
        # 2.1 Set weather for SimWorld
        weather = carla.WeatherParameters(cloudiness=10.0,
                                          precipitation=10.0,
                                          fog_density=10.0)
        world.set_weather(weather)

        # 2.2 Blueprint and Actor
        blueprint_library = world.get_blueprint_library()

        # 2.2.0 Generate a car
        # https://carla.readthedocs.io/en/latest/catalogue_vehicles/
        ego_vehicle_bp = blueprint_library.find('vehicle.tesla.cybertruck')
        if ego_vehicle_bp.has_attribute('color'):
            ego_vehicle_bp.set_attribute('color', '0, 0, 0')
        transform = random.choice(world.get_map().get_spawn_points())
        # spawn the vehicle
        ego_vehicle = world.spawn_actor(ego_vehicle_bp, transform)
        # set the vehicle autopilot mode
        ego_vehicle.set_autopilot()

        actor_list.append(ego_vehicle)

        # 2.2.1 Mount a camera on vehicle
        camera_bp = blueprint_library.find('sensor.camera.rgb')
        camera_transform = carla.Transform(carla.Location(x=1.5, z=2.4))
        # spawn the camera
        camera = world.spawn_actor(
            camera_bp, camera_transform, attach_to=ego_vehicle)

        # 2.2.2 Mount a lidar on vehicle
        lidar_bp = blueprint_library.find('sensor.lidar.ray_cast')
        lidar_bp.set_attribute('channels', str(32))
        lidar_bp.set_attribute('points_per_second', str(90000))
        lidar_bp.set_attribute('rotation_frequency', str(40))
        lidar_bp.set_attribute('range', str(20))

        lidar_xyz = carla.Location(0, 0, 2)
        lidar_rpy = carla.Rotation(0, 0, 0)
        lidar_transform = carla.Transform(lidar_xyz, lidar_rpy)
        # spawn the lidar.
        lidar = world.spawn_actor(
            lidar_bp, lidar_transform, attach_to=ego_vehicle)

        camera.listen(lambda image: sensor_processor.CameraCallback(image))
        # camera.listen(lambda image: image.save_to_disk(
        #     os.path.join(output_path, "camera", '%06d.png' % image.frame)))
        sensor_list.append(camera)

        # lidar.listen(lambda point_cloud: point_cloud.save_to_disk(
        #     os.path.join(output_path, "lidar", '%06d.ply' % point_cloud.frame)))
        sensor_list.append(lidar)

        while True:
            spectator = world.get_spectator()
            transform = ego_vehicle.get_transform()
            spectator.set_transform(carla.Transform(
                transform.location+carla.Location(z=20),
                carla.Rotation(pitch=-90)))

    finally:
        print('destroying actors')
        client.apply_batch([carla.command.DestroyActor(x) for x in actor_list])
        for sensor in sensor_list:
            sensor.destroy()
        print('done.')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Exited by user.")
