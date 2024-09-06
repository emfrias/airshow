import React, { useState, useEffect } from 'react';
import { View, ScrollView } from 'react-native';
import { Text, TextInput, Button, Card, IconButton, Checkbox, Menu, Provider, FAB } from 'react-native-paper';
import DraggableFlatList from 'react-native-draggable-flatlist';
import api from '../../api/api';

const CONDITION_TYPES = ['2d_distance', '3d_distance', 'aircraft_type', 'registration_number', 'aircraft_category'];

const FilterScreen = () => {
  const [filters, setFilters] = useState([]);
  const [menuVisible, setMenuVisible] = useState(false);
  const [dirtyFlags, setDirtyFlags] = useState({}); // Track which filters are dirty

  useEffect(() => {
    const fetchFilters = async () => {
      try {
        const response = await api.get('/api/user/filters');
        const fetchedFilters = response.data;
        setFilters(fetchedFilters);
        // Initialize dirty flags to false for all filters
        const flags = {};
        fetchedFilters.forEach(f => (flags[f.id] = false));
        setDirtyFlags(flags);
      } catch (error) {
        console.error("Error fetching filters", error);
      }
    };
    fetchFilters();
  }, []);

  // Mark a filter as dirty when modified
  const markDirty = (filterId) => {
    setDirtyFlags({ ...dirtyFlags, [filterId]: true });
  };

  // Save filter changes
  const handleSave = async (filter) => {
    try {
      await api.put(`/api/user/filters/${filter.id}`, filter);
      setDirtyFlags({ ...dirtyFlags, [filter.id]: false }); // Reset dirty flag on save
    } catch (error) {
      console.error("Error saving filter", error);
    }
  };

  // Add new filter
  const addNewFilter = async () => {
    try {
      const response = await api.post('/api/user/filters', {
        name: 'My Filter',
        conditions: [{ type: '2d_distance', value: { max_distance: 3 } }],
      });
      const newFilter = response.data;
      setFilters([...filters, newFilter]);
      setDirtyFlags({ ...dirtyFlags, [newFilter.id]: false });
    } catch (error) {
      console.error("Error adding new filter", error);
    }
  };

  const handleDelete = async (filterId) => {
    try {
      await api.delete(`/api/user/filters/${filterId}`);
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
    markDirty(filterId);
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
    markDirty(filterId);
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
    markDirty(filterId);
  };

  const updateFilterName = (filterId, newName) => {
    setFilters(filters.map(f => f.id === filterId ? { ...f, name: newName } : f));
    markDirty(filterId);
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
              onChangeText={(text) => updateConditionValue(filterId, conditionIndex, { max_distance: text })}
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
      <Card.Title
        title={
          <TextInput
            value={item.name}
            onChangeText={(text) => updateFilterName(item.id, text)}
            placeholder="Filter Name"
          />
        }
        left={() => <IconButton icon="drag" onPress={drag} />}
      />
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
          <Provider>
            <Menu
              visible={menuVisible}
              onDismiss={() => setMenuVisible(false)}
              anchor={<Button onPress={() => setMenuVisible(true)}>Add Condition</Button>}
            >
              {CONDITION_TYPES.filter(type => !item.conditions.some(c => c.type === type)).map(type => (
                <Menu.Item key={type} onPress={() => { addCondition(item.id, type); setMenuVisible(false); }} title={type.replace('_', ' ')} />
              ))}
            </Menu>
          </Provider>
        </ScrollView>
      </Card.Content>
      <Card.Actions>
        <Button onPress={() => handleSave(item)} mode="contained" disabled={!dirtyFlags[item.id]}>
          Save
        </Button>
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
        onDragEnd={({ data }) => {
          setFilters(data);
          data.forEach((filter, index) => {
            filter.evaluation_order = index + 1;
            markDirty(filter.id);
          });
        }}
      />
      <FAB
        style={{ position: 'absolute', margin: 16, right: 0, bottom: 0 }}
        icon="plus"
        onPress={addNewFilter}
      />
    </View>
  );
};

export default FilterScreen;
