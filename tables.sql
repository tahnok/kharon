CREATE TABLE outdoor_temperature (
        id serial,
        value float,
        observed_at timestamptz
    );
CREATE INDEX outdoor_temperature_date_idx ON outdoor_temperature(observed_at);

CREATE TABLE outdoor_humidity (
        id serial,
        value float,
        observed_at timestamptz
    );
CREATE INDEX outdoor_humidity_date_dix ON outdoor_humidity(observed_at);

