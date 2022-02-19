<?php
/*
# Copyright (c) 2022 Busana Apparel Group. All rights reserved.
#
# This product and it's source code is protected by patents, copyright laws and
# international copyright treaties, as well as other intellectual property
# laws and treaties. The product is licensed, not sold.
#
# The source code and sample programs in this package or parts hereof
# as well as the documentation shall not be copied, modified or redistributed
# without permission, explicit or implied, of the author.
#
# This module is part of Centric PLM Integration Bridge and is released under
# the Apache-2.0 License: https://www.apache.org/licenses/LICENSE-2.0
*/

class BaseMessage {

    protected $message_type = 0;
    protected $message_id = null;
    protected $module = null;
    protected $submodule = null;
    protected $params = array(null, null);
    protected $message_options = null;

    public function __construct($msg_type=0) {
        $this->message_type = $msg_type;
    }

    function set_message($module, $submodule) {
        $this->message_id = gen_uuid();
        $this->module = $module;
        $this->submodule = $submodule;
    }

    public function set_parameters($args, $kwargs) {
        $this->params = array($args, $kwargs);
    }

    public function set_message_options($options) {
        $this->message_options = $options;
    }
}

class BridgeCommandMessage extends BaseMessage {
    protected $command = null;

    public function __construct() {
        parent::__construct(0);
    }

    public function set_message($module, $submodule, $message) {
        parent::set_message($module, $submodule);
        $this->command = $message;
    }

    public function encode() {
        $message = array('msgtype' => $this->message_type,
            'msgid' => $this->message_id,
            'module' => $this->module,
            'submodule' => $this->submodule,
            'command' => $this->event,
            'data' => $this->params,
            'options' => $this->message_options);
        $command_str = json_encode($message);
        return base64_encode($command_str);
    }

}

class BridgeEventMessage extends BaseMessage {
    protected $event = null;

    public function __construct() {
        parent::__construct(1);
    }

    public function set_message($module, $submodule, $message) {
        parent::set_message($module, $submodule);
        $this->event = $message;
    }

    public function encode() {
        $message = array('msgtype' => $this->message_type,
            'msgid' => $this->message_id,
            'module' => $this->module,
            'submodule' => $this->submodule,
            'event' => $this->event,
            'data' => $this->params,
            'options' => $this->message_options);
        $event_str = json_encode($message);
        return base64_encode($event_str);
    }

}

function gen_uuid() {
    return sprintf( '%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
        // 32 bits for "time_low"
        mt_rand( 0, 0xffff ), mt_rand( 0, 0xffff ),

        // 16 bits for "time_mid"
        mt_rand( 0, 0xffff ),

        // 16 bits for "time_hi_and_version",
        // four most significant bits holds version number 4
        mt_rand( 0, 0x0fff ) | 0x4000,

        // 16 bits, 8 bits for "clk_seq_hi_res",
        // 8 bits for "clk_seq_low",
        // two most significant bits holds zero and one for variant DCE1.1
        mt_rand( 0, 0x3fff ) | 0x8000,

        // 48 bits for "node"
        mt_rand( 0, 0xffff ), mt_rand( 0, 0xffff ), mt_rand( 0, 0xffff )
    );
}
?>
