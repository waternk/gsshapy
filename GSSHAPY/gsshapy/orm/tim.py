"""
********************************************************************************
* Name: TimeSeriesModel
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""

__all__ = ['TimeSeriesFile',
           'TimeSeries',
           'TimeSeriesValue']

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Float, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.base.file_base import GsshaPyFileObjectBase
from gsshapy.lib.pivot import pivot


class TimeSeriesFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    Object interface for Time Series Files.

    This object stores information from several time series output files. There are two supporting objects that are used
    to store the contents of this file: :class:`.TimeSeries` and :class:`.TimeSeriesValue`.

    See:
    """

    __tablename__ = 'tim_time_series_files'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id'))  #: FK

    # Value Columns
    fileExtension = Column(String, default='txt')  #: STRING

    # Relationship Properties
    projectFile = relationship('ProjectFile', back_populates='timeSeriesFiles')  #: RELATIONSHIP
    timeSeries = relationship('TimeSeries', back_populates='timeSeriesFile')  #: RELATIONSHIP

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID):
        """
        Generic Time Series Read from File Method
        """
        # Assign file extension attribute to file object
        self.fileExtension = extension

        timeSeries = []

        # Open file and parse into a data structure
        with open(path, 'r') as f:
            for line in f:
                sline = line.strip().split()

                record = {'time': sline[0],
                          'values': []}

                for idx in range(1, len(sline)):
                    record['values'].append(sline[idx])

                timeSeries.append(record)

        self._createTimeSeriesObjects(timeSeries, filename)


    def _write(self, session, openFile):
        """
        Generic Time Series Write to File Method
        """
        # Retrieve all time series
        timeSeries = self.timeSeries

        # Num TimeSeries
        numTS = len(timeSeries)

        # Transform into list of dictionaries for pivot tool
        valList = []

        for tsNum, ts in enumerate(timeSeries):
            values = ts.values
            for value in values:
                valDict = {'time': value.simTime,
                           'tsNum': tsNum,
                           'value': value.value}
                valList.append(valDict)

        # Use pivot function (from lib) to pivot the values into 
        # a format that is easy to write.
        result = pivot(valList, ('time',), ('tsNum',), 'value')

        # Write lines
        for line in result:

            valString = ''
            # Compile value string
            for n in range(0, numTS):
                val = '%.6f' % line[(n,)]
                valString = '%s%s%s' % (
                    valString,
                    ' ' * (13 - len(str(val))),  # Fancy spacing trick
                    val)

            openFile.write('   %.8f%s\n' % (line['time'], valString))

    def _createTimeSeriesObjects(self, timeSeries, filename):
        """
        Create GSSHAPY TimeSeries and TimeSeriesValue Objects Method
        """
        try:
            # Determine number of value columns
            valColumns = len(timeSeries[0]['values'])

            # Create List of GSSHAPY TimeSeries objects
            series = []
            for i in range(0, valColumns):
                ts = TimeSeries()
                ts.timeSeriesFile = self
                series.append(ts)

            for record in timeSeries:
                for index, value in enumerate(record['values']):
                    # Create GSSHAPY TimeSeriesValue objects
                    tsVal = TimeSeriesValue(simTime=record['time'],
                                            value=value)

                    # Associate with appropriate TimeSeries object via the index
                    tsVal.timeSeries = series[index]
        except IndexError:
            print ('WARNING: %s was opened, but the contents of the file were empty.'
                   'This file will not be read into the database.') % filename
        except:
            raise


class TimeSeries(DeclarativeBase):
    """
    Object that stores data for a single time series in a time series file.

    Time series files can contain several time series datasets. The values for the times series are stored in
    :class:`.TimeSeriesValue` objects.
    """

    __tablename__ = 'tim_time_series'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    timeSeriesFileID = Column(Integer, ForeignKey('tim_time_series_files.id'))  #: FK

    # Relationship Properties
    timeSeriesFile = relationship('TimeSeriesFile', back_populates='timeSeries')  #: RELATIONSHIP
    values = relationship('TimeSeriesValue', back_populates='timeSeries')  #: RELATIONSHIP


class TimeSeriesValue(DeclarativeBase):
    """
    Object containing the data for a single time series value. Includes the time stamp and value.
    """

    __tablename__ = 'tim_time_series_values'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    timeSeriesID = Column(Integer, ForeignKey('tim_time_series.id'), nullable=False)  #: FK

    # Value Columns
    simTime = Column(Float, nullable=False)  #: FLOAT
    value = Column(Float, nullable=False)  #: FLOAT

    # Relationship Properties
    timeSeries = relationship('TimeSeries', back_populates='values')  #: RELATIONSHIP

    def __init__(self, simTime, value):
        """
        Constructor
        """
        self.simTime = simTime
        self.value = value

    def __repr__(self):
        return '<TimeSeriesValue: Time=%s, Value=%s>' % (self.simTime, self.value)