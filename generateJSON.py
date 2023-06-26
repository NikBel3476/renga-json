import os
from pathlib import Path
from uuid import UUID
from typing import Literal, Any
from domain.LevelElevation import LevelElevation
from domain.Room import Room
from domain.Point3D import Point3D
from domain.Geometry import Geometry
from domain.Stairway import Stairway
import win32com.client
import orjson


def is_in_edge(x: list[float], y: list[float], xp: list[float], yp: list[float]) -> bool:
    for idx in range(len(x)):
        for i in range(len(xp)):
            in_edge: bool = (
                xp[i] == xp[i - 1]
                and xp[i] == x[idx]
                and min(yp[i], yp[i - 1]) <= y[idx] <= max(yp[i], yp[i - 1])
            )
            if not in_edge:
                in_edge = (
                    yp[i] == yp[i - 1]
                    and yp[i] == y[idx]
                    and min(xp[i], xp[i - 1]) <= x[idx] <= max(xp[i], xp[i - 1])
                )
            if not in_edge:
                in_edge = min(yp[i], yp[i - 1]) <= y[idx] <= max(yp[i], yp[i - 1]) and min(
                    xp[i], xp[i - 1]
                ) <= x[idx] <= max(xp[i], xp[i - 1])
            if not in_edge:  # проверка вхождения точки в отрезок (Общее уравнение прямой)
                a = yp[i] - yp[i - 1]
                b = xp[i - 1] - xp[i]
                c = xp[i - 1] * yp[i] - xp[i] * yp[i - 1]
                in_edge = a * x[idx] + b * y[idx] + c == 0
            if in_edge:
                return in_edge
    return False


def is_in_edge_xyz(
    x: list[float],
    y: list[float],
    z: list[float],
    xp: list[float],
    yp: list[float],
    zp: list[float],
    door_size_z: float,
) -> bool:
    for idx in range(len(x)):
        for i in range(len(xp)):
            bot_door = max(zp) - door_size_z
            in_edge = (
                xp[i] == xp[i - 1]
                and xp[i] == x[idx]
                and min(yp[i], yp[i - 1]) <= y[idx] <= max(yp[i], yp[i - 1])
                and bot_door <= z[idx] <= max(zp)
            )
            if not in_edge:
                in_edge = (
                    yp[i] == yp[i - 1]
                    and yp[i] == y[idx]
                    and min(xp[i], xp[i - 1]) <= x[idx] <= max(xp[i], xp[i - 1])
                    and bot_door <= z[idx] <= max(zp)
                )
            if not in_edge:
                in_edge = (
                    min(yp[i], yp[i - 1]) <= y[idx] <= max(yp[i], yp[i - 1])
                    and min(xp[i], xp[i - 1]) <= x[idx] <= max(xp[i], xp[i - 1])
                    and bot_door <= z[idx] <= max(zp)
                )
            # if not inEdge:           проверка вхождения точки в отрезок (Общее уравнение прямой)
            #    a = yp[i] - yp[i-1]
            #    b = xp[i-1] - xp[i]
            #    c = xp[i-1]*yp[i] - xp[i]*yp[i-1]
            #    inEdge = (a*x[idx]+b*y[idx]+c == 0)
            if in_edge:
                return in_edge
    return False


def get_coord(build_elem) -> dict[Literal["X", "Y"], list[float]]:
    x: list[float] = []
    y: list[float] = []

    if isinstance(build_elem, Room):
        for i in range(len(build_elem.xy[0].points)):
            x.append(build_elem.xy[0].points[i].x)
            y.append(build_elem.xy[0].points[i].y)
    else:
        for i in range(len(build_elem["XY"][0]["points"])):
            x.append(build_elem["XY"][0]["points"][i]["x"])
            y.append(build_elem["XY"][0]["points"][i]["y"])
    return {"X": x, "Y": y}


def in_door(door_size_z, z_stair, z_door):
    for stair in z_stair:
        for door in z_door:
            if door - door_size_z <= stair <= door:
                print(f"door - doorSizeZ {door - door_size_z} <= stair {stair} <= door {door}")
                return True


def main():
    app = win32com.client.Dispatch("Renga.Application.1")

    app.Visible = True

    resource_dir_name = "resources"
    file_name = "school11v3_latest"
    file_extension = ".rnp"
    current_dir = os.path.dirname(os.path.realpath(__file__))
    renga_file_path = os.path.join(current_dir, resource_dir_name, file_name + file_extension)
    app.OpenProject(renga_file_path)
    project = app.Project
    model = project.Model
    object_collection = model.GetObjects()
    # GUID for the 'level' object type, as listed in documentation. See "Object types".
    level_type = "{c3ce17ff-6f28-411f-b18d-74fe957b2ba8}".upper()
    room_type = "{f1a805ff-573d-f46b-ffba-57f4bccaa6ed}".upper()
    # "{4329112a-6b65-48d9-9da8-abf1f8f36327}".upper()
    # "{f5bd8bd8-39c1-47f8-8499-f673c580dfbe}".upper()
    door_type = "{1cfba99c-01e7-4078-ae1a-3e2ff0673599}".upper()
    # "{386ee889-38aa-4016-9e62-6b893f99ce43}".upper()
    stair_type = "{3f522f49-aee2-4d73-9866-9b07cf336a69}".upper()
    # r = win32com.client.Record("GridTypes", 0)
    # print(project.DataExporter.GetObjects3D().Get(2).GetMesh(0).GetGrid(0).GetVertex(0))
    objects3d_collection = project.DataExporter.GetObjects3D()  # Экспортируем все объекты

    rooms_data: list[Room] = []
    doors_data = []
    stairs_data: list[Stairway] = []
    level_data: list[LevelElevation] = []

    def level():
        for idx in range(object_collection.Count):
            object = object_collection.GetByIndex(idx)
            if object.ObjectTypeS == level_type:
                parameter_container = object.GetParameters()
                level_elevation = "{440a20f8-42b8-4a5f-9000-39ef58e0302b}".upper()
                # for i in range(parameterContainer.GetIds().Count):
                level_name = "{1bb1addf-a3c0-4356-9525-107ea7df1513}".upper()
                level_data.append(
                    LevelElevation(
                        parameter_container.GetS(level_elevation).GetDoubleValue(),
                        parameter_container.GetS(level_name).GetStringValue(),
                    )
                )
                print(parameter_container.GetS(level_elevation).GetDoubleValue())
                print(parameter_container.GetS(level_name).GetStringValue())
                # levelModel = object.GetInterfaceByName("ILevel")

    def get_coord_stairs():
        net_floor_area = "{ea60d526-b527-4896-8e4c-c84a8462b3cc}".upper()  # Площадь
        stair_height = "{6eb5fbe0-3b56-484b-8dde-06de32187a66}".upper()  # Высота лестницы
        level_elevation = "{440a20f8-42b8-4a5f-9000-39ef58e0302b}".upper()
        level_id = "{8cdf2e5b-03f7-4101-9b43-93b9da18f411}".upper()
        for i in range(objects3d_collection.Count):
            object3_d = objects3d_collection.Get(i)
            if object3_d.ModelObjectTypeS == stair_type:
                points: list[Point3D] = []
                object_id = object3_d.ModelObjectId

                quantities_container = object_collection.GetById(object_id).GetQuantities()
                parameter_container = object_collection.GetById(object_id).GetParameters()

                level = object_collection.GetById(parameter_container.GetS(level_id).GetIntValue())

                points_z: list[float] = []
                for j in range(object3_d.GetMesh(0).GridCount):  # У комнаты 1 меш
                    gridStair = object3_d.GetMesh(0).GetGrid(j)  # разбиваем комнаты на грид

                    if gridStair.GridType == 1:  # идентификатор верхней плоскости лестницы
                        for k in range(gridStair.VertexCount):  # Перебираем вершины
                            points.append(
                                Point3D(
                                    x=gridStair.GetVertex(k).X,
                                    y=gridStair.GetVertex(k).Y,
                                    z=gridStair.GetVertex(k).Z,
                                )
                            )
                            points_z.append(gridStair.GetVertex(k).Z)

                print(len(points_z))
                min_point_z = min(points_z)
                max_point_z = max(points_z)
                polygon_points_stair: list[Point3D] = []
                for point in points:  # Выбираем самые низкие и высокие точки летницы
                    if point not in polygon_points_stair and (
                        point.z == min_point_z or point.z == max_point_z
                    ):
                        polygon_points_stair.append(point)

                stair = Stairway(
                    sign="Staircase",
                    output=[],
                    id=UUID(object_collection.GetById(object_id).UniqueIdS),
                    name=object_collection.GetById(object_id).Name,
                    area=quantities_container.GetS(net_floor_area).AsArea(3),
                    sizeZ=parameter_container.GetS(stair_height).GetDoubleValue() / 1000,
                    zLevel=level.GetParameters().GetS(level_elevation).GetDoubleValue(),
                    xy=[Geometry(polygon_points_stair)],
                )

                if str(stair.id) == "9b2524dc-c42d-409e-8957-a0435fc99f4f":
                    print(*points, sep="\n")
                    print(f"min: {min_point_z}")
                    print(f"max: {max_point_z}")

                stairs_data.append(stair)

    get_coord_stairs()

    def get_coord_room() -> dict[Literal["xPoints", "yPoints"], list[Point3D]]:
        x_points: list[Point3D] = []
        y_points: list[Point3D] = []
        room_height = "{187c61e7-26dd-40e3-aeb6-3274aec082d2}".upper()
        net_floor_area = "{ea60d526-b527-4896-8e4c-c84a8462b3cc}".upper()  # Площадь
        level_id = "{8cdf2e5b-03f7-4101-9b43-93b9da18f411}".upper()
        level_elevation = "{440a20f8-42b8-4a5f-9000-39ef58e0302b}".upper()

        for i in range(objects3d_collection.Count):
            object3d = objects3d_collection.Get(i)
            if object3d.ModelObjectTypeS == room_type:  # Ищем меши комнаты
                object_id = object3d.ModelObjectId
                object_collection.GetById(object_id).UniqueId
                object_collection.GetById(object_id)

                quantities_container = object_collection.GetById(object_id).GetQuantities()
                parameter_container = object_collection.GetById(object_id).GetParameters()

                level = object_collection.GetById(parameter_container.GetS(level_id).GetIntValue())

                room = Room(
                    sign="Room",
                    outputs=[],
                    id=UUID(object_collection.GetById(object_id).UniqueIdS),
                    name=object_collection.GetById(object_id).Name,
                    area=quantities_container.GetS(net_floor_area).AsArea(3),
                    size_z=parameter_container.GetS(room_height).GetDoubleValue() / 1000,
                    z_level=level.GetParameters().GetS(level_elevation).GetDoubleValue(),
                    xy=[Geometry([])],
                )

                # добавление вершин
                for j in range(object3d.GetMesh(0).GridCount):  # У комнаты 1 меш
                    grid_room = object3d.GetMesh(0).GetGrid(j)  # разбиваем комнаты на грид
                    if grid_room.GridType == 1:  # идентификатор пола, ищем пол комнаты
                        for k in range(grid_room.VertexCount):  # Перебираем вершины
                            room.xy[0].points.append(
                                Point3D(
                                    grid_room.GetVertex(k).X,
                                    grid_room.GetVertex(k).Y,
                                    grid_room.GetVertex(k).Z,
                                )
                            )
                        # points.append(points[0]) # замыкающая точка полигона
                rooms_data.append(room)
        return {"xPoints": x_points, "yPoints": y_points}

    def get_coord_door():
        x_points = []
        y_points = []
        for i in range(objects3d_collection.Count):
            # print(f'сколько всего обжект 3Д коллекшн{Objects3DCollection.Count}')
            # print(project.DataExporter.GetObjects3D().Get(6).ModelObjectTypeS)
            object3d = objects3d_collection.Get(i)
            if object3d.ModelObjectTypeS == door_type:  # Ищем меши комнаты
                door = {}
                points = []
                object_id = object3d.ModelObjectId
                door["Sign"] = "Door"
                door["Output"] = []
                id_string = object_collection.GetById(object_id).UniqueIdS
                door["Id"] = id_string[1 : len(id_string) - 1]
                # door['Id'] = id_string
                door["@"] = id_string[1 : len(id_string) - 1]
                door["Name"] = object_collection.GetById(object_id).Name
                parameter_container = object_collection.GetById(object_id).GetParameters()
                level_id = "{8cdf2e5b-03f7-4101-9b43-93b9da18f411}".upper()
                level_elevation = "{440a20f8-42b8-4a5f-9000-39ef58e0302b}".upper()
                # LevelName = '{1bb1addf-a3c0-4356-9525-107ea7df1513}'.upper()
                door_width = "{569911cd-d708-4274-bc17-107c6a5d47a1}".upper()
                door_height = "{eae12886-6635-4292-b46e-e1a15b5df263}".upper()
                # ParentObjectName = '{26f7604a-ebaa-449c-8305-2ab01273d0eb}'.upper()
                # ParentObjectUniqueId = '{0d915b9f-2c28-4c3a-9d9f-4055fb7de95a}'.upper()
                # print(objectCollection.GetById(parameterContainer.GetS(LevelId).GetIntValue()).UniqueIdS)
                level = object_collection.GetById(parameter_container.GetS(level_id).GetIntValue())
                # door['roomLevelName'] = level.GetParameters().GetS(LevelName).GetStringValue()
                door["ZLevel"] = level.GetParameters().GetS(level_elevation).GetDoubleValue()
                print(parameter_container.GetS(level_id).GetIntValue())
                door["Width"] = parameter_container.GetS(door_width).GetDoubleValue() / 1000
                door["SizeZ"] = parameter_container.GetS(door_height).GetDoubleValue()
                points_z = []
                # print(f'мешей у двери{Object3D.GetMesh(0).GetGrid(0)}')
                # for j in range(Object3D.GetMesh(0).GridCount): # У комнаты 1 меш
                for j in range(object3d.GetMesh(0).GridCount):  # У комнаты 1 меш
                    grid_room = object3d.GetMesh(0).GetGrid(j)  # разбиваем комнаты на грид
                    if grid_room.GridType == 4:  # идентификатор пола, ищем пол комнаты
                        for k in range(grid_room.VertexCount):  # Перебираем вершины
                            points.append(
                                {
                                    "x": grid_room.GetVertex(k).X,
                                    "y": grid_room.GetVertex(k).Y,
                                    "z": grid_room.GetVertex(k).Z,
                                }
                            )
                            points_z.append(grid_room.GetVertex(k).Z)
                            # FIXME: Ломается определение свзязей при переходе к метрам
                            # points.append({
                            # 'x': gridRoom.GetVertex(k).X / 1000,
                            # 'y': gridRoom.GetVertex(k).Y / 1000,
                            #    'z': gridRoom.GetVertex(k).Z / 1000})
                            # pointsZ.append(gridRoom.GetVertex(k).Z / 1000)
                            # print(f'Дверь {gridRoom.GetVertex(k)}')
                            # xPoints.push(gridRoom.GetVertex(k).X)
                            # yPoints.push(gridRoom.GetVertex(k).Y)
                        # points.append(points[0])
                max_point_z = max(points_z)
                polygon_points_stair = []
                for point in points:
                    if point["z"] == max_point_z and point not in polygon_points_stair:
                        polygon_points_stair.append(point)
                door["XY"] = [{"points": polygon_points_stair}]
                # pprint(door)
                doors_data.append(door)
        return {"xPoints": x_points, "yPoints": y_points}

    get_coord_room()
    get_coord_door()

    # level()
    # pprint(f'Уровни {levelData}')

    def get_coord_xyz(build_elem) -> dict[Literal["X", "Y", "Z"], list[float]]:
        X: list[float] = []
        Y: list[float] = []
        Z: list[float] = []

        if isinstance(build_elem, Stairway):
            for i in range(len(build_elem.xy[0].points)):
                X.append(build_elem.xy[0].points[i].x)
                Y.append(build_elem.xy[0].points[i].y)
                Z.append(build_elem.xy[0].points[i].z)
        else:
            for i in range(len(build_elem["XY"][0]["points"])):
                X.append(build_elem["XY"][0]["points"][i]["x"])
                Y.append(build_elem["XY"][0]["points"][i]["y"])
                Z.append(build_elem["XY"][0]["points"][i]["z"])
        return {"X": X, "Y": Y, "Z": Z}

    # def get_building_info():
    #     building_info = project.BuildingInfo()
    #     building_info.GetAddres()
    #     return building_info

    def bond_obj():
        level = []

        for room in rooms_data:
            room_points = get_coord(room)
            for door in doors_data:
                door_points = get_coord(door)
                if room.zLevel == door["ZLevel"]:
                    if is_in_edge(
                        door_points["X"], door_points["Y"], room_points["X"], room_points["Y"]
                    ):
                        room.output.append(door["Id"])
                        door["Output"].append(room.id)
                if len(door["Output"]) < 2:
                    door["Sign"] = "DoorWayOut"
                else:
                    door["Sign"] = "DoorWayInt"

        for stair in stairs_data:
            stair_points = get_coord_xyz(stair)
            for door in doors_data:
                door_points = get_coord_xyz(door)
                if is_in_edge_xyz(
                    stair_points["X"],
                    stair_points["Y"],
                    stair_points["Z"],
                    door_points["X"],
                    door_points["Y"],
                    door_points["Z"],
                    door["SizeZ"],
                ):
                    stair.output.append(door["Id"])
                    door["Output"].append(stair.id)
                if len(door["Output"]) < 2:
                    door["Sign"] = "DoorWayOut"
                else:
                    door["Sign"] = "DoorWayInt"

        # pprint(roomsData)
        # pprint(doorsData)
        build_element: list[Any] = rooms_data + doors_data + stairs_data

        # pprint(f' door id  {getCoord(doorsData[0])}')
        # pprint(f' rooms id  {getCoord(roomsData[0])}')

        # pprint(BuildElement)

        for elevation in level_data:
            temp_level: list[Any] = []
            for idx in range(len(build_element)):
                try:
                    element = build_element[idx]
                    if isinstance(element, Room) or isinstance(element, Stairway):
                        if element.zLevel == elevation.levelZ:
                            temp_level.append(element)
                    else:
                        if element["ZLevel"] == elevation.levelZ:
                            element.pop("ZLevel")
                            temp_level.append(element)
                except KeyError:
                    continue
            level.append(
                {
                    "Name": elevation.levelName,
                    "SizeZ": elevation.levelZ / 1000,
                    "BuildElement": temp_level,
                }
            )
        # pprint(level)

        jsn = {
            "nameBuilding": project.BuildingInfo.Name,
            "program_name": "Программа создания файла JSON",
            "address_building": {
                "city": project.BuildingInfo.GetAddress().Town,
                "streetAddress": "",
                "addInfo": "",
                "country": project.BuildingInfo.GetAddress().Country,
                "region": project.BuildingInfo.GetAddress().Region,
                "postcode": project.BuildingInfo.GetAddress().Postcode,
            },
            "Level": level,
            "Devs": [],
        }

        Path(resource_dir_name).mkdir(parents=True, exist_ok=True)
        out_file_path = os.path.join(resource_dir_name, f"{file_name}.json")
        with open(out_file_path, "wb") as jsonf:
            json_string = orjson.dumps(
                jsn,
                option=orjson.OPT_INDENT_2
                | orjson.OPT_SERIALIZE_DATACLASS
                | orjson.OPT_SERIALIZE_UUID,
            )
            _ = jsonf.write(json_string)

    level()
    bond_obj()

    result = app.CloseProject(1)
    if result != 0:
        print("Error closing project")

    app.Quit()


if __name__ == "__main__":
    main()
