# _*_ coding: utf-8 _*_
import time
import sys
import numpy as np
import xml.etree.ElementTree as ET
import rti.connextdds as dds
from dds.AIEP_AIEP_ import SGEODETIC_POSITION
from dds.AIEP_AIEP_ import CMSHCI_AIEP_M_MINE_SELECTED_PLAN, CMSHCI_AIEP_M_MINE_DROPPING_PLAN_REQ, AIEP_INTERNAL_INFER_REQ, TEWA_ASSIGN_CMD, NAVINF_SHIP_NAVIGATION_INFO, CMSHCI_AIEP_PA_INFO, CMSHCI_AIEP_WPN_GEO_WAYPOINTS,CMSHCI_AIEP_AI_WAYPOINTS_INFERENCE_REQ, CMSHCI_AIEP_M_MINE_EDITED_PLAN_LIST, NAVINF_SHIP_NAVIGATION_INFO, TEWA_WA_TUBE_LOAD_INFO, TRKMGR_SYSTEMTARGET_INFO, AIEP_WPN_CTRL_STATUS_INFO
from dds.AIEP_AIEP_ import CMSHCI_AIEP_WPN_CTRL_CMD

import numpy as np
import matplotlib.pyplot as plt

class MYPublisher:
    participant = None
    provider = None
    qos_mapping = {}
    data_AIEP_INTERNAL_INFER_REQ = None
  
    @staticmethod
    def load_qos_mapping():
        tree = ET.parse("MY_QOS_PROFILES.xml")
        root = tree.getroot()
            
        for profile in root.findall('.//qos_profile'):
            name = profile.get('name')
            base = profile.get('base_name')
            if name and base:
                MYPublisher.qos_mapping[name] = base
                print(f"Mapped: {name} -> {base}")


    @staticmethod
    def get_message_qos(message_name):
        base_profile = MYPublisher.qos_mapping.get(message_name)
        
        if base_profile:
            try:
                topic_qos = MYPublisher.provider.topic_qos_from_profile(base_profile)
                writer_qos = MYPublisher.provider.datawriter_qos_from_profile(base_profile)
                print(f"Loaded QoS for {message_name}: {base_profile}")
                return topic_qos, writer_qos
            except Exception as e:
                print(f"QoS load failed for {message_name}: {e}")
        else:
            print(f"No QoS mapping found for {message_name}, using default")
        
        return dds.TopicQos(), dds.DataWriterQos()

    @staticmethod
    def initialize_participant(domain_id: int):
        if MYPublisher.participant is None:
            try:
                MYPublisher.provider = dds.QosProvider("file://MY_QOS_PROFILES.xml")

                MYPublisher.load_qos_mapping()

                MYPublisher.participant_qos = MYPublisher.provider.participant_qos_from_profile("k1pqos::ParticipantQos")                
                MYPublisher.participant = dds.DomainParticipant(domain_id, qos=MYPublisher.participant_qos)

                MYPublisher.create_all_topics_and_writers()
                
            except Exception as e:
                print(f"Initialization error: {e}")
                MYPublisher.participant = dds.DomainParticipant(domain_id)
                  
    @staticmethod
    def create_all_topics_and_writers():
        message_classes = [
            CMSHCI_AIEP_M_MINE_EDITED_PLAN_LIST,
            CMSHCI_AIEP_M_MINE_SELECTED_PLAN,
            CMSHCI_AIEP_M_MINE_DROPPING_PLAN_REQ,
            CMSHCI_AIEP_PA_INFO,
            CMSHCI_AIEP_WPN_CTRL_CMD,
            CMSHCI_AIEP_WPN_GEO_WAYPOINTS,
            CMSHCI_AIEP_AI_WAYPOINTS_INFERENCE_REQ,
            TEWA_ASSIGN_CMD,
            TEWA_WA_TUBE_LOAD_INFO,
            TRKMGR_SYSTEMTARGET_INFO,
            NAVINF_SHIP_NAVIGATION_INFO,
            TEWA_WA_TUBE_LOAD_INFO, 
            AIEP_INTERNAL_INFER_REQ,
            AIEP_WPN_CTRL_STATUS_INFO
        ]
        
        for message_class in message_classes:
            message_name = message_class.__name__ 
            topic_qos, writer_qos = MYPublisher.get_message_qos(message_name)

            topic = dds.Topic(MYPublisher.participant, message_name, message_class, qos=topic_qos)
            setattr(MYPublisher, f"topic{message_name}", topic)

            writer = dds.DataWriter(MYPublisher.participant.implicit_publisher, topic, qos=writer_qos)
            setattr(MYPublisher, f"writer{message_name}", writer)
                
            print(f"Created topic{message_name} and writer{message_name}")

    @staticmethod
    def publish_CMSHCI_AIEP_M_MINE_DROPPING_PLAN_REQ():
        message = CMSHCI_AIEP_M_MINE_DROPPING_PLAN_REQ()
        message.bDroppingPlanReq = bool( 1 )

        MYPublisher.writerCMSHCI_AIEP_M_MINE_DROPPING_PLAN_REQ.write(message)
        print("writerCMSHCI_AIEP_M_MINE_DROPPING_PLAN_REQ is sent")

    @staticmethod
    def publish_TEWA_ASSIGN_CMD(data):
        MYPublisher.writerTEWA_ASSIGN_CMD.write(data)

    @staticmethod
    def publish_NAVINF_SHIP_NAVIGATION_INFO(data):
        """Publish ownship navigation info"""
        MYPublisher.writerNAVINF_SHIP_NAVIGATION_INFO.write(data)
        print("NAVINF_SHIP_NAVIGATION_INFO sent")

    @staticmethod
    def publish_TEWA_WA_TUBE_LOAD_INFO(data):
        """Publish tube load info"""
        MYPublisher.writerTEWA_WA_TUBE_LOAD_INFO.write(data)
        print(f"TEWA_WA_TUBE_LOAD_INFO sent for Tube {data.eTubeNum}")
