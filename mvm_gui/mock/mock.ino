#include <StandardCplusplus.h>

// If this fails, install ArduinoSTL from the Arduino library
// and use the following instead:
// #include <ArduinoSTL.h>

#include <map>
#include <vector>
#include <algorithm> // std::find
#include <SoftwareSerial.h>

SoftwareSerial Debug(2, 3); // RX, TX

// change it to \n in case of line termination is not \n\r
auto const terminator = '\r';
auto const separator = ' ';

std::map<String, String> parameters;

std::vector<String> random_measures;

namespace mvm {

struct Seconds
{
  static
  unsigned long from_millis(unsigned long milli)
  {
    return milli / 1000ul;
  }

  static
  unsigned long from_micros(unsigned long micro)
  {
    return micro / 1000000ul;
  }
};

template<class Time>
unsigned long now()
{
  return Time::from_micros(micros());
}

size_t send(Stream& connection, String const& data)
{
  auto const header = String("valore=");
  auto const len = header.length() + data.length();

  auto sent = connection.print(header);

  auto pos = data.c_str();

  while (sent != len) {
    auto const to_be_sent = len - sent;
    auto const nbytes
      = to_be_sent > SERIAL_TX_BUFFER_SIZE
      ? SERIAL_TX_BUFFER_SIZE
      : to_be_sent;

    auto const written = connection.write(pos, nbytes);
    pos += written;
    sent += written;
  }

  sent += connection.println("");

  return sent;
}

using alarm_t = uint32_t;

alarm_t raise_hw_alarm(int num, alarm_t alarm)
{
  alarm_t const alarm_bit = 1 << num;

  return alarm | alarm_bit;
}

alarm_t snooze_hw_alarm(int num, alarm_t alarm)
{
  alarm_t const alarm_bit = 1 << num;
  alarm_t const mask = 0xFFFFFFFF ^ alarm_bit;

  return alarm & mask;
}

alarm_t set_gui_alarm(alarm_t alarm)
{
  alarm_t constexpr gui_alarm_bit = 1 << 29;

  return alarm | gui_alarm_bit;
}

} // ns mvm

mvm::alarm_t alarm_status = 0;
mvm::alarm_t warning_status = 0;

unsigned long pause_lg_expiration = mvm::now<mvm::Seconds>() + 10;
unsigned long gui_watchdog_expr = mvm::now<mvm::Seconds>() + 5;

void setup()
{
  Serial.begin(115200);
  while (!Serial);
  Serial.setTimeout(50000);
  Debug.begin(115200);

  random_measures = { "pressure", "bpm", "flow", "o2", "tidal", "peep",
                      "temperature", "power_mode", "battery" };

  parameters["run"]    = String(0);
  parameters["mode"]   = String(0);
  parameters["backup"] = String(0);
  parameters["wdenable"] = String(0);

  parameters["pcv_trigger"]        = String(5);
  parameters["pcv_trigger_enable"] = String(0);

  parameters["rate"]             = String(12);
  parameters["ratio"]            = String(2);
  parameters["ptarget"]          = String(15);
  parameters["assist_ptrigger"]  = String(1);
  parameters["assist_flow_min"]  = String(20);
  parameters["pressure_support"] = String(10);
  parameters["backup_enable"]    = String(1);
  parameters["backup_min_time"]  = String(10);
  parameters["pause_lg_time"]    = String(10);
  parameters["pause_lg_p"]       = String(10);
}

// this is tricky, didn't had the time to think a better algo
String parse_word(String const& command)
{
  auto const first_sep_pos = command.indexOf(separator);
  if (first_sep_pos == -1) {
    return command;
  }

  auto const second_sep_pos = command.indexOf(separator, first_sep_pos + 1);

  return command.substring(first_sep_pos + 1, second_sep_pos);
}

String set(String const& command)
{
  auto const name = parse_word(command);
  auto const value = parse_word(command.substring(name.length() + 4));

  if (name == "alarm") {
    if (value == "0") {
      alarm_status = 0;
    } else if (value == "1") {
      alarm_status = mvm::set_gui_alarm(alarm_status);
    } else {
      return "notok";
    }
    return "OK";
  } else if (name == "alarm_snooze") {
    alarm_status = mvm::snooze_hw_alarm(value.toInt(), alarm_status);
    return "OK";
  } else if (name == "warning" && value == "0") {
    warning_status = 0;
    return "OK";
  } else if (name == "_hwalarm") {
    alarm_status = mvm::raise_hw_alarm(value.toInt(), alarm_status);
    return "OK";
  } else if (name == "_hwwarning") {
    warning_status = mvm::raise_hw_alarm(value.toInt(), warning_status);
    return "OK";
  } else if (name == "wdenable" && value == "1") {
    gui_watchdog_expr = mvm::now<mvm::Seconds>() + 5;
    alarm_status = mvm::snooze_hw_alarm(30, alarm_status);
  }

  parameters[name] = value;

  if (name == "pause_lg" && value == "1") {
    pause_lg_expiration
    = mvm::now<mvm::Seconds>()
    + parameters["pause_lg_time"].toInt();
  }

  return "OK";
}

String get(String const& command)
{
  auto const name = parse_word(command);

  if (name == "all") {
    return
        String(random(20, 70))     + "," // pressure
      + String(random(3, 21))      + "," // flow
      + String(random(30, 100))    + "," // o2
      + String(random(6, 8))       + "," // bpm
      + String(random(1000, 1500)) + "," // tidal
      + String(random(4, 20))      + "," // peep
      + String(random(10, 50))     + "," // temperature
      + String(random(0, 1))       + "," // power_mode
      + String(random(20, 100))    + "," // battery
      + String(random(70, 80))     + "," // peak
      + String(random(1000, 2000)) + "," // total_inspired_volume
      + String(random(1000, 2000)) + "," // total_expired_volume
      + String(random(10, 100));         // volume_minute
  } else if (name == "pause_lg_time") {
    auto const now = mvm::now<mvm::Seconds>();
    return now > pause_lg_expiration ? "0" : String(pause_lg_expiration - now);
  } else if (name == "alarm") {
    return String(alarm_status);
  } else if (name == "warning") {
    return String(warning_status);
  } else if (name == "version") {
    return "mock";
  }

  auto const it = std::find(
      random_measures.begin()
    , random_measures.end()
    , name
  );

  if (it != random_measures.end()) {
    return String(random(10, 100));
  } else {
    auto const it = parameters.find(name);

    return it == parameters.end() ? String("unknown") : it->second;
  }
}

void serial_loop(Stream& connection)
{
  if (connection.available() > 0) {
    String command = connection.readStringUntil(terminator);
    command.trim();
    auto const command_type = command.substring(0, 3);

    if (command.length() == 0) {
    } else if (command_type == "get") {
      mvm::send(connection, get(command));
    } else if (command_type == "set") {
      mvm::send(connection, set(command));
    } else {
      mvm::send(connection, "notok");
    }
  }
}

void loop()
{
  serial_loop(Serial);
  serial_loop(Debug);

  if (parameters["wdenable"] == "1") {
    auto const now = mvm::now<mvm::Seconds>();
    if (now > gui_watchdog_expr) {
      alarm_status = mvm::raise_hw_alarm(30, alarm_status);
    }
  }
}
