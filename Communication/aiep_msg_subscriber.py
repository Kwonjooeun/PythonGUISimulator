
import time
import sys
import xml.etree.ElementTree as ET
import rti.connextdds as dds
from typing import cast
from dds.AIEP_AIEP_ import (
        AIEP_INTERNAL_INFER_RESULT_FIRE_TIME,
        AIEP_WPN_CTRL_STATUS_INFO,
        AIEP_CMSHCI_M_MINE_ALL_PLAN_LIST,
        AIEP_M_MINE_EP_RESULT,
        AIEP_AI_INFER_RESULT_WP,
        AIEP_ALM_ASM_EP_RESULT,
        AIEP_WGT_EP_RESULT,
        AIEP_AAM_EP_RESULT,
        CMSHCI_AIEP_PA_INFO,
        CMSHCI_AIEP_WPN_GEO_WAYPOINTS
)
from Communication.aiep_msg_publisher import MYPublisher

class MySubscriber:
    participant = None
    provider = None
    qos_mapping = {}
    readers = {}

    @staticmethod
    def load_qos_mapping():
        tree = ET.parse("MY_QOS_PROFILES.xml")
        root = tree.getroot()
            
        for profile in root.findall('.//qos_profile'):
            name = profile.get('name')
            base = profile.get('base_name')
            if name and base:
                MySubscriber.qos_mapping[name] = base

    @staticmethod
    def get_message_qos(message_name):
        base_profile = MySubscriber.qos_mapping.get(message_name)
        
        if base_profile:
            try:
                topic_qos = MySubscriber.provider.topic_qos_from_profile(base_profile)
                reader_qos = MySubscriber.provider.datareader_qos_from_profile(base_profile)
                print(f"Subscriber loaded QoS for {message_name}: {base_profile}")
                return topic_qos, reader_qos
            except Exception as e:
                print(f"Subscriber QoS load failed for {message_name}: {e}")
        else:
            print(f"No QoS mapping found for {message_name}, using default")
        
        return dds.TopicQos(), dds.DataReaderQos()

    @staticmethod
    def initialize_participant(domain_id: int):
        if MySubscriber.participant is None:
            try:
                MySubscriber.provider = dds.QosProvider("file://MY_QOS_PROFILES.xml")
                MySubscriber.load_qos_mapping()
                
                # Participant 생성 (Publisher와 동일한 QoS 사용)
                participant_qos = MySubscriber.provider.participant_qos_from_profile("k1pqos::ParticipantQos")                
                MySubscriber.participant = dds.DomainParticipant(domain_id, qos=participant_qos)
                
                MySubscriber.create_all_topics_and_readers()
                
            except Exception as e:
                print(f"Subscriber initialization error: {e}")
                MySubscriber.participant = dds.DomainParticipant(domain_id)

    @staticmethod
    def create_all_topics_and_readers():
            
        message_classes = [
            AIEP_INTERNAL_INFER_RESULT_FIRE_TIME,
            AIEP_WPN_CTRL_STATUS_INFO,
            AIEP_CMSHCI_M_MINE_ALL_PLAN_LIST,
            AIEP_M_MINE_EP_RESULT,
            AIEP_AI_INFER_RESULT_WP,
            AIEP_ALM_ASM_EP_RESULT,
            AIEP_WGT_EP_RESULT,
            AIEP_AAM_EP_RESULT,
            CMSHCI_AIEP_PA_INFO,
            CMSHCI_AIEP_WPN_GEO_WAYPOINTS
        ]
        
            
        for message_class in message_classes:
            message_name = message_class.__name__
            topic_qos, reader_qos = MySubscriber.get_message_qos(message_name)
            
            # Topic 생성
            topic = dds.Topic(MySubscriber.participant, message_name, message_class, qos=topic_qos)
            setattr(MySubscriber, f"topic{message_name}", topic)
            
            # Reader 생성
            reader = dds.DataReader(MySubscriber.participant.implicit_subscriber, topic, qos=reader_qos)
            setattr(MySubscriber, f"reader{message_name}", reader)
            
            # readers 딕셔너리에도 저장 (기존 코드 호환성)
            MySubscriber.readers[message_name] = reader
            
            # data_{MESSAGE_NAME} 속성 초기화
            # 교전계획 결과 메시지는 딕셔너리로 초기화 (tube_num을 키로 사용)
            if message_name in ['AIEP_M_MINE_EP_RESULT', 'AIEP_ALM_ASM_EP_RESULT', 
                                 'AIEP_WGT_EP_RESULT', 'AIEP_AAM_EP_RESULT']:
                setattr(MySubscriber, f"data_{message_name}", {})  # 딕셔너리로 초기화
            else:
                setattr(MySubscriber, f"data_{message_name}", None)
            
            print(f"Created topic{message_name}, reader{message_name}, and data_{message_name}")
    

    @staticmethod
    def process_data(reader):
        # take_data() returns copies of all the data samples in the reader
        # and removes them. To also take the SampleInfo meta-data, use take().
        # To not remove the data from the reader, use read_data() or read().
        samples = reader.take_data()
        for sample in samples:
            # 전체 자항기뢰 부설계획 목록
            if isinstance(sample, AIEP_CMSHCI_M_MINE_ALL_PLAN_LIST):
                MySubscriber.data_AIEP_CMSHCI_M_MINE_ALL_PLAN_LIST = cast(AIEP_CMSHCI_M_MINE_ALL_PLAN_LIST, sample)
                print('[Rcvd] AIEP_CMSHCI_M_MINE_ALL_PLAN_LIST')

            # 자항기뢰 교전계획 산출 결과 - 딕셔너리에 저장
            if isinstance(sample, AIEP_M_MINE_EP_RESULT):
                tube_num = sample.enTubeNum
                MySubscriber.data_AIEP_M_MINE_EP_RESULT[tube_num] = cast(AIEP_M_MINE_EP_RESULT, sample)
                print(f'[Rcvd] AIEP_M_MINE_EP_RESULT from Tube {tube_num}')
    
            # ALM/ASM EP Result - 딕셔너리에 저장
            if isinstance(sample, AIEP_ALM_ASM_EP_RESULT):
                tube_num = sample.enTubeNum
                MySubscriber.data_AIEP_ALM_ASM_EP_RESULT[tube_num] = cast(AIEP_ALM_ASM_EP_RESULT, sample)
                print(f'[Rcvd] AIEP_ALM_ASM_EP_RESULT from Tube {tube_num}')
        
            # WGT EP Result - 딕셔너리에 저장
            if isinstance(sample, AIEP_WGT_EP_RESULT):
                tube_num = sample.enTubeNum
                MySubscriber.data_AIEP_WGT_EP_RESULT[tube_num] = cast(AIEP_WGT_EP_RESULT, sample)
                print(f'[Rcvd] AIEP_WGT_EP_RESULT from Tube {tube_num}')
        
            # AAM EP Result - 딕셔너리에 저장
            if isinstance(sample, AIEP_AAM_EP_RESULT):
                tube_num = sample.eTubeNum
                MySubscriber.data_AIEP_AAM_EP_RESULT[tube_num] = cast(AIEP_AAM_EP_RESULT, sample)
                print(f'[Rcvd] AIEP_AAM_EP_RESULT from Tube {tube_num}')


            if isinstance(sample, AIEP_INTERNAL_INFER_RESULT_FIRE_TIME):
                MySubscriber.data_AIEP_INTERNAL_INFER_RESULT_FIRE_TIME = cast(AIEP_INTERNAL_INFER_RESULT_FIRE_TIME, sample)
                
            if isinstance(sample, AIEP_AI_INFER_RESULT_WP):
                MySubscriber.data_AIEP_AI_INFER_RESULT_WP = cast(AIEP_AI_INFER_RESULT_WP, sample)

                message = CMSHCI_AIEP_WPN_GEO_WAYPOINTS()
                message.eTubeNum = MySubscriber.data_AIEP_AI_INFER_RESULT_WP.eTubeNum
                message.eWpnKind = MySubscriber.data_AIEP_AI_INFER_RESULT_WP.eWpnKind
                message.stGeoWaypoints = MySubscriber.data_AIEP_AI_INFER_RESULT_WP.stGeoWaypoints

                MYPublisher.writerCMSHCI_AIEP_WPN_GEO_WAYPOINTS.write(message)
                
            if isinstance(sample, AIEP_WPN_CTRL_STATUS_INFO):
                MySubscriber.data_AIEP_WPN_CTRL_STATUS_INFO = cast(AIEP_WPN_CTRL_STATUS_INFO, sample)
                
                tubeNum = MySubscriber.data_AIEP_WPN_CTRL_STATUS_INFO.eTubeNum
                ctrlState = MySubscriber.data_AIEP_WPN_CTRL_STATUS_INFO.eCtrlState
                wpnTime = MySubscriber.data_AIEP_WPN_CTRL_STATUS_INFO.wpnTime
                print(f"[Rcvd] AIEP_WPN_CTRL_STATUS_INFO.eTubeNum={tubeNum},eCtrlState={ctrlState},wpnTime={wpnTime}]")

        return len(samples)

    @staticmethod
    def run_subscriber(domain_id: int, sample_count: int):
        MySubscriber.initialize_participant(domain_id)
        samples_read = {topic_name: 0 for topic_name in MySubscriber.readers.keys()}

        def condition_handler(_):
            """Handler for processing data when status condition is triggered."""
            nonlocal samples_read
            for topic_name, reader in MySubscriber.readers.items():
                samples_read[topic_name] += MySubscriber.process_data(reader)

        # Create a WaitSet and attach StatusConditions for all readers
        waitset = dds.WaitSet()

        for topic_name, reader in MySubscriber.readers.items():
            # Obtain the DataReader's Status Condition
            status_condition = dds.StatusCondition(reader)

            # Enable the "data available" status and set the handler.
            status_condition.enabled_statuses = dds.StatusMask.DATA_AVAILABLE
            status_condition.set_handler(condition_handler)

            # Attach the StatusCondition to the WaitSet
            waitset += status_condition

        # Main loop to wait for data
        print("Waiting for data...")
        while any(count < sample_count for count in samples_read.values()):
            waitset.dispatch(dds.Duration(1))  # Wait for 1 second intervals
            print(".",end='',flush=True)
        print("Sample count reached for all topics:")
        for topic_name, count in samples_read.items():
            print(f"  {topic_name}: {count} samples")
