import React, { useState, useEffect } from 'react';
import { View,  ScrollView } from 'react-native';
import { Text, TextInput, Button, Card, IconButton, Checkbox } from 'react-native-paper';
import DraggableFlatList from 'react-native-draggable-flatlist';
import api from '../../api/api';

const CONDITION_TYPES = ['2d_distance', '3d_distance', 'aircraft_type', 'registration_number', 'aircraft_category'];

const FilterScreen = () => {
  const [filters, setFilters] = useState([]);

  useEffect(() => {
    const fetchFilters = async () => {
      try {
        const response = await api.get('/api/user/filters');
        setFilters(response.data);
      } catch (error) {
        console.error("Error fetching filters", error);
      }
    };
    fetchFilters();
  }, []);

  const handleSave = async (filter) => {
    try {
      await api.put(`/user/filters/${filter.id}`, filter);
    } catch (error) {
      console.error("Error saving filter", error);
    }
  };

  const handleDelete = async (filterId) => {
    try {
      await api.delete(`/user/filters/${filterId}`);
      setFilters(filters.filter(f => f.id !== filterId));
    } catch (error) {
      console.error("Error deleting filter", error);
    }
  };

  const addCondition = (filterId, type) => {
    setFilters(filters.map(f => {
      if (f.id === filterId) {
        return {
          ...f,
          conditions: [...f.conditions, { type, value: '' }]
        };
      }
      return f;
    }));
  };

  const removeCondition = (filterId, conditionIndex) => {
    setFilters(filters.map(f => {
      if (f.id === filterId) {
        const updatedConditions = [...f.conditions];
        updatedConditions.splice(conditionIndex, 1);
        return {
          ...f,
          conditions: updatedConditions,
        };
      }
      return f;
    }));
  };

  const updateConditionValue = (filterId, conditionIndex, value) => {
    setFilters(filters.map(f => {
      if (f.id === filterId) {
        const updatedConditions = [...f.conditions];
        updatedConditions[conditionIndex].value = value;
        return { ...f, conditions: updatedConditions };
      }
      return f;
    }));
  };

  const renderCondition = (condition, filterId, conditionIndex) => {
    switch (condition.type) {
      case '2d_distance':
      case '3d_distance':
        return (
          <View>
            <Text>{condition.type.replace('_', ' ')} (Nautical Miles)</Text>
            <TextInput
              keyboardType="numeric"
              value={condition.value.max_distance}
              onChangeText={(text) => updateConditionValue(filterId, conditionIndex, {max_distance: text})}
            />
          </View>
        );
      case 'angle_above_horizon':
        return (
          <View>
            <Text>Angle above the horizon (degrees)</Text>
            <TextInput
              keyboardType="numeric"
              value={condition.value.min_angle}
              onChangeText={(text) => updateConditionValue(filterId, conditionIndex, {min_angle: text})}
            />
          </View>
        );
      case 'aircraft_type':
      case 'registration_number':
        return (
          <View>
            <Text>{condition.type.replace('_', ' ')} (Comma-separated list)</Text>
            <TextInput
              value={condition.value}
              onChangeText={(text) => updateConditionValue(filterId, conditionIndex, text)}
              multiline
            />
          </View>
        );
      case 'aircraft_category':
        return (
          <View>
            <Text>Aircraft Category (Select multiple)</Text>
            {/* Replace with your own list of categories */}
            <Checkbox.Item
              label="Category A"
              status={condition.value.includes('A') ? 'checked' : 'unchecked'}
              onPress={() => updateConditionValue(filterId, conditionIndex, 'A')}
            />
            <Checkbox.Item
              label="Category B"
              status={condition.value.includes('B') ? 'checked' : 'unchecked'}
              onPress={() => updateConditionValue(filterId, conditionIndex, 'B')}
            />
          </View>
        );
      default:
        return null;
    }
  };

  const renderItem = ({ item, drag }) => (
    <Card style={{ margin: 10 }}>
      <Card.Title title={item.name} left={() => <IconButton icon="drag" onPress={drag} />} />
      <Card.Content>
        <ScrollView>
          {item.conditions.map((condition, index) => (
            <View key={index} style={{ marginBottom: 10 }}>
              {renderCondition(condition, item.id, index)}
              <Button onPress={() => removeCondition(item.id, index)} mode="contained" disabled={item.conditions.length === 1 && (condition.type === '2d_distance' || condition.type === '3d_distance')}>
                Remove Condition
              </Button>
            </View>
          ))}
          <Button onPress={() => addCondition(item.id, '2d_distance')}>Add Distance Condition</Button>
          <Button onPress={() => addCondition(item.id, 'aircraft_type')}>Add Other Condition</Button>
        </ScrollView>
      </Card.Content>
      <Card.Actions>
        <Button onPress={() => handleSave(item)} mode="contained">Save</Button>
        <Button onPress={() => handleDelete(item.id)} mode="outlined">Delete</Button>
      </Card.Actions>
    </Card>
  );

  return (
    <View style={{ flex: 1, padding: 10 }}>
      <Text style={{ fontSize: 24, textAlign: 'center', marginBottom: 20 }}>Your Filters</Text>
      <DraggableFlatList
        data={filters}
        renderItem={renderItem}
        keyExtractor={(item) => item.id.toString()}
        onDragEnd={({ data }) => setFilters(data)}
      />
    </View>
  );
};

export default FilterScreen;

