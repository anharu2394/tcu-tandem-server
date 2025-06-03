from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TandemData(_message.Message):
    __slots__ = ("id", "timestamp", "beam_current_in", "beam_current_out", "charge_current", "gvm", "charge_power_supply", "le", "he", "cpo", "probe_current", "probe_position", "experiment_id", "transmission_ratio", "transmission_slope", "transmission_variance", "beam_loss_ratio", "gvm_charge_slope", "gvm_charge_variance", "gvm_charge_correlation", "charge_current_slope", "charge_current_variance", "gvm_slope", "gvm_variance", "le_he_difference", "probe_current_slope", "probe_current_variance", "score_1", "score_2", "score_3", "score_4", "score_5", "stability_score")
    ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    BEAM_CURRENT_IN_FIELD_NUMBER: _ClassVar[int]
    BEAM_CURRENT_OUT_FIELD_NUMBER: _ClassVar[int]
    CHARGE_CURRENT_FIELD_NUMBER: _ClassVar[int]
    GVM_FIELD_NUMBER: _ClassVar[int]
    CHARGE_POWER_SUPPLY_FIELD_NUMBER: _ClassVar[int]
    LE_FIELD_NUMBER: _ClassVar[int]
    HE_FIELD_NUMBER: _ClassVar[int]
    CPO_FIELD_NUMBER: _ClassVar[int]
    PROBE_CURRENT_FIELD_NUMBER: _ClassVar[int]
    PROBE_POSITION_FIELD_NUMBER: _ClassVar[int]
    EXPERIMENT_ID_FIELD_NUMBER: _ClassVar[int]
    TRANSMISSION_RATIO_FIELD_NUMBER: _ClassVar[int]
    TRANSMISSION_SLOPE_FIELD_NUMBER: _ClassVar[int]
    TRANSMISSION_VARIANCE_FIELD_NUMBER: _ClassVar[int]
    BEAM_LOSS_RATIO_FIELD_NUMBER: _ClassVar[int]
    GVM_CHARGE_SLOPE_FIELD_NUMBER: _ClassVar[int]
    GVM_CHARGE_VARIANCE_FIELD_NUMBER: _ClassVar[int]
    GVM_CHARGE_CORRELATION_FIELD_NUMBER: _ClassVar[int]
    CHARGE_CURRENT_SLOPE_FIELD_NUMBER: _ClassVar[int]
    CHARGE_CURRENT_VARIANCE_FIELD_NUMBER: _ClassVar[int]
    GVM_SLOPE_FIELD_NUMBER: _ClassVar[int]
    GVM_VARIANCE_FIELD_NUMBER: _ClassVar[int]
    LE_HE_DIFFERENCE_FIELD_NUMBER: _ClassVar[int]
    PROBE_CURRENT_SLOPE_FIELD_NUMBER: _ClassVar[int]
    PROBE_CURRENT_VARIANCE_FIELD_NUMBER: _ClassVar[int]
    SCORE_1_FIELD_NUMBER: _ClassVar[int]
    SCORE_2_FIELD_NUMBER: _ClassVar[int]
    SCORE_3_FIELD_NUMBER: _ClassVar[int]
    SCORE_4_FIELD_NUMBER: _ClassVar[int]
    SCORE_5_FIELD_NUMBER: _ClassVar[int]
    STABILITY_SCORE_FIELD_NUMBER: _ClassVar[int]
    id: str
    timestamp: _timestamp_pb2.Timestamp
    beam_current_in: float
    beam_current_out: float
    charge_current: float
    gvm: str
    charge_power_supply: float
    le: float
    he: float
    cpo: float
    probe_current: float
    probe_position: float
    experiment_id: str
    transmission_ratio: float
    transmission_slope: float
    transmission_variance: float
    beam_loss_ratio: float
    gvm_charge_slope: float
    gvm_charge_variance: float
    gvm_charge_correlation: float
    charge_current_slope: float
    charge_current_variance: float
    gvm_slope: float
    gvm_variance: float
    le_he_difference: float
    probe_current_slope: float
    probe_current_variance: float
    score_1: float
    score_2: float
    score_3: float
    score_4: float
    score_5: float
    stability_score: float
    def __init__(self, id: _Optional[str] = ..., timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., beam_current_in: _Optional[float] = ..., beam_current_out: _Optional[float] = ..., charge_current: _Optional[float] = ..., gvm: _Optional[str] = ..., charge_power_supply: _Optional[float] = ..., le: _Optional[float] = ..., he: _Optional[float] = ..., cpo: _Optional[float] = ..., probe_current: _Optional[float] = ..., probe_position: _Optional[float] = ..., experiment_id: _Optional[str] = ..., transmission_ratio: _Optional[float] = ..., transmission_slope: _Optional[float] = ..., transmission_variance: _Optional[float] = ..., beam_loss_ratio: _Optional[float] = ..., gvm_charge_slope: _Optional[float] = ..., gvm_charge_variance: _Optional[float] = ..., gvm_charge_correlation: _Optional[float] = ..., charge_current_slope: _Optional[float] = ..., charge_current_variance: _Optional[float] = ..., gvm_slope: _Optional[float] = ..., gvm_variance: _Optional[float] = ..., le_he_difference: _Optional[float] = ..., probe_current_slope: _Optional[float] = ..., probe_current_variance: _Optional[float] = ..., score_1: _Optional[float] = ..., score_2: _Optional[float] = ..., score_3: _Optional[float] = ..., score_4: _Optional[float] = ..., score_5: _Optional[float] = ..., stability_score: _Optional[float] = ...) -> None: ...
